"""Ghost CFO Agent — entry point.

Usage (after install):
    GhostCFOAgent.exe --run          # single manual run
    GhostCFOAgent.exe --install ...  # install as Windows service
    GhostCFOAgent.exe --uninstall    # remove service
    GhostCFOAgent.exe --service      # called internally by NSSM / scheduler

Configuration is read from  C:\\GhostCFO\\config.json  (written by --install).
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from connector import evolution_db
from sync.encryptor import encrypt_payload
from sync.extractor import extract
from sync.uploader import upload_snapshot

CONFIG_PATH = Path(r"C:\GhostCFO\config.json")
LOG_PATH = Path(r"C:\GhostCFO\agent.log")

# Ensure the install directory exists before opening the log file
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_PATH}. Run --install first.")
    with CONFIG_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)


def _run_sync(
    cfg: dict,
    period_month: int | None = None,
    period_year: int | None = None,
) -> None:
    log.info("=== Ghost CFO Agent — sync starting ===")
    server         = cfg["sql_server"]
    db             = cfg["sql_db"]
    username       = cfg.get("sql_username", "")
    password       = cfg.get("sql_password", "")
    api_key        = cfg["api_key"]
    encryption_key = cfg["encryption_key"]
    base_url       = cfg.get("base_url", "https://ghostcfo.numbers10.co.za")

    if period_month and period_year:
        log.info("Target period: %02d/%d (manual override)", period_month, period_year)
    else:
        log.info("Target period: previous month (automatic)")

    log.info("Connecting to Pastel Evolution: %s / %s (user: %s)", server, db, username or "Windows auth")
    with evolution_db.connect(server=server, database=db, username=username, password=password) as conn:
        log.info("Connection OK — extracting financial data…")
        data = extract(conn, period_month=period_month, period_year=period_year)

    log.info(
        "Extraction complete — period %02d/%d",
        data["period_month"], data["period_year"],
    )

    log.info("Encrypting payload…")
    payload_b64 = encrypt_payload(data, encryption_key)

    log.info("Uploading to %s …", base_url)
    result = upload_snapshot(payload_b64, api_key, base_url)
    log.info("Upload accepted — server response: %s", result)
    log.info("=== Ghost CFO Agent — sync complete ===")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        click.echo("Ghost CFO Agent. Use --help for commands.")


@cli.command()
@click.option("--month", type=click.IntRange(1, 12), default=None,
              help="Month to pull (1-12). Defaults to previous month.")
@click.option("--year", type=click.IntRange(2000, 2099), default=None,
              help="Year to pull, e.g. 2026. Defaults to current/previous year.")
def run(month: int | None, year: int | None) -> None:
    """Run a single sync immediately.

    Examples:
        GhostCFOAgent.exe run                        # pulls previous month automatically
        GhostCFOAgent.exe run --month 3 --year 2026  # pulls March 2026 specifically
    """
    if (month is None) != (year is None):
        raise click.UsageError("Provide both --month and --year, or neither.")
    cfg = _load_config()
    _run_sync(cfg, period_month=month, period_year=year)


@cli.command()
def poll() -> None:
    """Send heartbeat + SQL status, check for pending on-demand sync requests.

    Called every 5 minutes by the GhostCFOAgentPoll scheduled task.
    Exits after completing — Task Scheduler handles the repeat interval.
    """
    cfg = _load_config()
    base_url = cfg.get("base_url", "https://ghostcfo.numbers10.co.za")
    api_key = cfg["api_key"]

    # Test SQL Server connection so the dashboard can show SQL status
    sql_ok: bool | None = None
    try:
        sql_ok = evolution_db.test_connection(
            server=cfg["sql_server"],
            database=cfg["sql_db"],
            username=cfg.get("sql_username", ""),
            password=cfg.get("sql_password", ""),
        )
        log.debug("SQL connection test: %s", "OK" if sql_ok else "FAILED")
    except Exception as exc:
        log.warning("SQL connection test raised: %s", exc)
        sql_ok = False

    # Send heartbeat with SQL status
    from sync.uploader import send_heartbeat
    send_heartbeat(api_key, base_url, sql_ok=sql_ok)

    # Check for pending on-demand sync (set by admin via Force Sync)
    from service.scheduler import _check_pending
    pending = _check_pending(cfg)
    if pending:
        month, year = pending
        log.info("Pending sync request: %02d/%d — running now.", month, year)
        _run_sync(cfg, period_month=month, period_year=year)
    else:
        log.debug("No pending sync requests.")


@cli.command()
def service() -> None:
    """Legacy: start long-running scheduler (monthly + poll threads). Kept for compatibility."""
    cfg = _load_config()
    from service.scheduler import run_scheduler
    run_scheduler(cfg)


@cli.command()
@click.option("--api-key", required=True, help="Ghost CFO API key for this client.")
@click.option("--server", required=True, help="SQL Server hostname or IP\\instance.")
@click.option("--db", required=True, help="Pastel Evolution database name.")
@click.option("--username", required=True, help="SQL Server login username.")
@click.option("--password", required=True, help="SQL Server login password.")
@click.option("--encryption-key", required=True, help="AES-256 encryption key (from Ghost CFO admin).")
@click.option("--base-url", default="https://ghostcfo.numbers10.co.za",
              show_default=True, help="Ghost CFO backend URL.")
def install(api_key: str, server: str, db: str, username: str, password: str,
            encryption_key: str, base_url: str) -> None:
    """Save config and install the Windows scheduled task."""
    cfg = {
        "api_key": api_key,
        "sql_server": server,
        "sql_db": db,
        "sql_username": username,
        "sql_password": password,
        "encryption_key": encryption_key,
        "base_url": base_url,
    }
    _save_config(cfg)
    log.info("Config saved to %s", CONFIG_PATH)

    # Test the SQL connection before installing the service
    log.info("Testing SQL Server connection…")
    if evolution_db.test_connection(server, db, username, password):
        log.info("SQL connection OK.")
        click.echo("[OK] SQL Server connection successful.")
    else:
        click.echo("[WARN] SQL Server connection test failed — check server/db/credentials.")
        click.echo("       The agent will still be installed; fix credentials in C:\\GhostCFO\\config.json")

    from service.installer import install_service
    install_service()


@cli.command()
def uninstall() -> None:
    """Remove the Windows service."""
    from service.installer import uninstall_service
    uninstall_service()


@cli.command()
def tray() -> None:
    """Run the system tray status icon (launched at Windows login by the installer)."""
    from tray import run_tray
    run_tray()


@cli.command()
def test_connection() -> None:
    """Test the SQL Server connection and print the number of GL transactions found."""
    cfg = _load_config()
    server = cfg["sql_server"]
    db_name = cfg["sql_db"]
    log.info("Testing connection: %s / %s", server, db_name)
    with evolution_db.connect(server=server, database=db_name) as conn:
        rows = evolution_db.run_query(
            conn,
            "SELECT COUNT(*) AS cnt FROM _btblGLTransactions",
        )
    count = rows[0]["cnt"] if rows else 0
    log.info("Connection OK — %d GL transactions in database.", count)
    click.echo(f"OK — {count} GL transactions found.")


if __name__ == "__main__":
    cli()
