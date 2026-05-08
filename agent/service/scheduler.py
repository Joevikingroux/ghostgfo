"""Lightweight fallback scheduler for environments where schtasks is unavailable.

Run with:  GhostCFOAgent.exe scheduler

This process stays resident and fires the sync on the 1st of each month at 06:00.
Use Windows Task Scheduler (installer.py) in production — this is a fallback only.
"""
from __future__ import annotations

import datetime
import logging
import time

log = logging.getLogger(__name__)


def _next_run_dt() -> datetime.datetime:
    """Return the datetime of the next 1st-of-month 06:00."""
    now = datetime.datetime.now()
    # First of next month
    if now.month == 12:
        target = datetime.datetime(now.year + 1, 1, 1, 6, 0, 0)
    else:
        target = datetime.datetime(now.year, now.month + 1, 1, 6, 0, 0)
    # If it's the 1st and we haven't passed 06:00 yet, run today
    if now.day == 1 and now.hour < 6:
        target = datetime.datetime(now.year, now.month, 1, 6, 0, 0)
    return target


def run_scheduler() -> None:
    """Block forever, sleeping until the next scheduled run."""
    log.info("Ghost CFO Agent scheduler started (fallback mode).")
    while True:
        target = _next_run_dt()
        wait_seconds = (target - datetime.datetime.now()).total_seconds()
        log.info("Next sync scheduled for %s (in %.1f hours).",
                 target.strftime("%Y-%m-%d %H:%M"), wait_seconds / 3600)
        if wait_seconds > 0:
            time.sleep(wait_seconds)

        log.info("Firing scheduled sync…")
        try:
            from main import _load_config, _run_sync  # noqa: PLC0415
            cfg = _load_config()
            _run_sync(cfg)
        except Exception as exc:
            log.exception("Scheduled sync failed: %s", exc)

        # Sleep briefly to avoid re-triggering within the same minute
        time.sleep(70)
