"""Monthly scheduler + hourly pending-sync poller for the Ghost CFO Agent.

Two jobs run in parallel threads:
  1. Monthly run — fires on the 1st of each month at 06:00, pulls previous month.
  2. Hourly poll  — checks /api/agent/status every 60 minutes. If the portal has
     set a pending sync request (bookkeeper uploaded payroll files and clicked
     "Generate Report"), runs a sync for that specific period immediately.

Run with:  GhostCFOAgent.exe scheduler
"""
from __future__ import annotations

import datetime
import logging
import threading
import time

import httpx

log = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS  = 5 * 60  # 5 minutes — pending sync poll
_HEARTBEAT_INTERVAL_SEC = 5 * 60  # 5 minutes — liveness ping


def _next_monthly_run() -> datetime.datetime:
    now = datetime.datetime.now()
    if now.month == 12:
        target = datetime.datetime(now.year + 1, 1, 1, 6, 0, 0)
    else:
        target = datetime.datetime(now.year, now.month + 1, 1, 6, 0, 0)
    if now.day == 1 and now.hour < 6:
        target = datetime.datetime(now.year, now.month, 1, 6, 0, 0)
    return target


def _check_pending(cfg: dict) -> tuple[int, int] | None:
    """Poll /api/agent/status and return (month, year) if a sync is pending, else None."""
    base_url = cfg.get("base_url", "https://ghostcfo.numbers10.co.za")
    url = base_url.rstrip("/") + "/api/agent/status"
    try:
        resp = httpx.get(
            url,
            headers={"X-Agent-Key": cfg["api_key"]},
            timeout=15,
            verify=True,
        )
        resp.raise_for_status()
        data = resp.json()
        month = data.get("pending_sync_month")
        year = data.get("pending_sync_year")
        if month and year:
            return int(month), int(year)
    except Exception as exc:
        log.warning("Pending-sync poll failed: %s", exc)
    return None


def _monthly_thread(cfg: dict) -> None:
    log.info("Monthly scheduler thread started.")
    while True:
        target = _next_monthly_run()
        wait = (target - datetime.datetime.now()).total_seconds()
        log.info("Next monthly sync at %s (in %.1f h).", target.strftime("%Y-%m-%d %H:%M"), wait / 3600)
        if wait > 0:
            time.sleep(wait)

        log.info("Monthly sync firing…")
        try:
            from main import _load_config, _run_sync  # noqa: PLC0415
            _run_sync(cfg)
        except Exception as exc:
            log.exception("Monthly sync failed: %s", exc)

        time.sleep(70)


def _poll_thread(cfg: dict) -> None:
    log.info("Hourly poll thread started (interval=%ds).", _POLL_INTERVAL_SECONDS)
    while True:
        time.sleep(_POLL_INTERVAL_SECONDS)
        log.debug("Polling for pending sync requests…")
        pending = _check_pending(cfg)
        if pending:
            month, year = pending
            log.info("Pending sync request found: %02d/%d — running now.", month, year)
            try:
                from main import _run_sync  # noqa: PLC0415
                _run_sync(cfg, period_month=month, period_year=year)
            except Exception as exc:
                log.exception("On-demand sync for %02d/%d failed: %s", month, year, exc)
        else:
            log.debug("No pending sync request.")


def _heartbeat_thread(cfg: dict) -> None:
    from sync.uploader import send_heartbeat  # noqa: PLC0415
    base_url = cfg.get("base_url", "https://ghostcfo.numbers10.co.za")
    api_key  = cfg["api_key"]
    log.info("Heartbeat thread started (interval=%ds).", _HEARTBEAT_INTERVAL_SEC)
    while True:
        send_heartbeat(api_key, base_url)
        time.sleep(_HEARTBEAT_INTERVAL_SEC)


def run_scheduler(cfg: dict) -> None:
    """Start all threads and block forever."""
    t_monthly   = threading.Thread(target=_monthly_thread,   args=(cfg,), daemon=True, name="monthly")
    t_poll      = threading.Thread(target=_poll_thread,      args=(cfg,), daemon=True, name="poll")
    t_heartbeat = threading.Thread(target=_heartbeat_thread, args=(cfg,), daemon=True, name="heartbeat")
    t_monthly.start()
    t_poll.start()
    t_heartbeat.start()
    log.info("Ghost CFO Agent scheduler running (monthly + poll + heartbeat).")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        log.info("Scheduler stopped.")
