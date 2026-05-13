"""Telegram delivery via Bot API.

Sends the monthly report summary as a plain text message to the business
owner's Telegram chat. The owner must message the bot first to obtain their
chat_id — stored on the Company record as owner_telegram.
"""

from __future__ import annotations

import calendar
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.narrative.tone import currency

log = get_logger(__name__)

_SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"
_MAX_CHARS = 4096  # Telegram text message limit


def _build_message(
    company_name: str,
    metrics: dict[str, Any],
    narrative_summary: str | None,
    narrative_actions: str | None,
) -> str:
    month = metrics.get("period_month", "?")
    year = metrics.get("period_year", "?")
    month_name = calendar.month_name[int(month)] if str(month).isdigit() else str(month)

    score = metrics.get("health_score", 0)
    rating = (metrics.get("health_rating") or "").upper()

    lines = [
        f"*Ghost CFO — {company_name}*",
        f"_{month_name} {year} Financial Report_",
        "",
        f"Health score: *{score}/100* ({rating})",
        "",
    ]

    if narrative_summary:
        lines.append(narrative_summary)
        lines.append("")

    rev = metrics.get("revenue_current_month", 0)
    rev_chg = metrics.get("revenue_change_pct", 0)
    cash = metrics.get("cash_balance", 0)
    runway = metrics.get("cash_runway_weeks", 0)
    overdue_count = metrics.get("overdue_invoices_count", 0)
    overdue_val = metrics.get("overdue_invoices_value", 0)

    lines += [
        f"• Revenue: {currency(rev)} ({rev_chg:+.1f}% vs last month)",
        f"• Cash: {currency(cash)} ({runway:.1f} weeks runway)",
    ]
    if overdue_count:
        lines.append(
            f"• ⚠ {overdue_count} overdue invoice(s) — {currency(overdue_val)}"
        )

    payroll = metrics.get("payroll_gross_total", 0)
    if payroll:
        pct = metrics.get("payroll_pct_of_revenue", 0)
        cash_covers = metrics.get("cash_covers_payroll", True)
        lines.append(f"• Payroll: {currency(payroll)} ({pct:.1f}% of revenue)")
        if not cash_covers:
            lines.append("• 🔴 URGENT: Cash may not cover next payroll run")

    if narrative_actions:
        lines += ["", "*Action items:*", narrative_actions]

    lines += [
        "",
        f"_Full PDF report sent by email\\. {settings.brand_footer}_",
    ]

    return "\n".join(lines)[:_MAX_CHARS]


def send_telegram_message(
    *,
    chat_id: str,
    company_name: str,
    metrics: dict[str, Any],
    narrative_summary: str | None,
    narrative_actions: str | None,
) -> bool:
    """Send a report summary message to a Telegram chat. Returns True on success."""
    if not settings.telegram_bot_token:
        log.warning("telegram.skipped", reason="TELEGRAM_BOT_TOKEN not set")
        return False

    if not chat_id:
        log.warning("telegram.skipped", reason="empty chat_id")
        return False

    text = _build_message(company_name, metrics, narrative_summary, narrative_actions)
    url = _SEND_URL.format(token=settings.telegram_bot_token)

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
            )

        if resp.status_code == 200:
            log.info(
                "telegram.sent", chat_id=chat_id[:4] + "****", company=company_name
            )
            return True

        log.warning(
            "telegram.api_error",
            status=resp.status_code,
            body=resp.text[:200],
        )
        return False
    except Exception as exc:
        log.error("telegram.failed", error=str(exc))
        return False
