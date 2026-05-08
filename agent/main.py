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


def _run_sync(cfg: dict) -> None:
    log.info("=== Ghost CFO Agent — sync starting ===")
    server = cfg["sql_server"]
    db = cfg["sql_db"]
    api_key = cfg["api_key"]
    encryption_key = cfg["encryption_key"]
    base_url = cfg.get("base_url", "https://ghostcfo.numbers10.co.za")

    log.info("Connecting to Pastel Evolution: %s / %s", server, db)
    with evolution_db.connect(server=server, database=db) as conn:
        log.info("Connection OK — extracting financial data…")
        data = extract(conn)

    log.info(
        "Extraction complete — period %d/%d, %d income rows",
        data["period_month"], data["period_year"],
        len(data.get("income_totals", {})),
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
def run() -> None:
    """Run a single sync immediately."""
    cfg = _load_config()
    _run_sync(cfg)


@cli.command()
def service() -> None:
    """Entry point called by NSSM / the Windows service wrapper on schedule."""
    cfg = _load_config()
    _run_sync(cfg)


@cli.command()
@click.option("--api-key", required=True, help="Ghost CFO API key for this client.")
@click.option("--server", required=True, help="SQL Server hostname or IP.")
@click.option("--db", required=True, help="Pastel Evolution database name.")
@click.option("--encryption-key", required=True, help="32-byte AES encryption key.")
@click.option("--base-url", default="https://ghostcfo.numbers10.co.za",
              show_default=True, help="Ghost CFO backend URL.")
def install(api_key: str, server: str, db: str, encryption_key: str, base_url: str) -> None:
    """Save config and install the Windows service via NSSM."""
    cfg = {
        "api_key": api_key,
        "sql_server": server,
        "sql_db": db,
        "encryption_key": encryption_key,
        "base_url": base_url,
    }
    _save_config(cfg)
    log.info("Config saved to %s", CONFIG_PATH)

    from service.installer import install_service
    install_service()


@cli.command()
def uninstall() -> None:
    """Remove the Windows service."""
    from service.installer import uninstall_service
    uninstall_service()


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
