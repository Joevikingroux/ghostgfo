"""WhatsApp delivery via Meta Cloud API.

Sends a plain-text narrative summary (≤1,024 chars) to the business owner.
Template messages require Meta approval for first-time contact — this module
sends a free-form text message valid within the 24-hour conversation window.
For cold delivery, a pre-approved template should be registered; that is
handled in a future phase.
"""

from __future__ import annotations

import calendar
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.narrative.tone import currency

log = get_logger(__name__)

_API_URL = "https://graph.facebook.com/v19.0/{phone_number_id}/messages"
_MAX_CHARS = 1024


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

    # Key metrics in compact form
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
        "_Full PDF report in your email. Reply STOP to unsubscribe._",
        f"_{settings.brand_footer}_",
    ]

    text = "\n".join(lines)
    # Hard truncate if still over limit, preserving brand footer
    if len(text) > _MAX_CHARS:
        text = text[: _MAX_CHARS - 3] + "..."
    return text


def send_whatsapp_message(
    *,
    to_number: str,
    company_name: str,
    metrics: dict[str, Any],
    narrative_summary: str | None,
    narrative_actions: str | None,
) -> bool:
    """Send the monthly pulse message. Returns True on success."""
    if not settings.whatsapp_phone_number_id or not settings.whatsapp_access_token:
        log.warning("whatsapp.skipped", reason="WHATSAPP credentials not configured")
        return False

    # Normalise number: ensure it starts with country code, no +
    number = to_number.replace(" ", "").replace("-", "").lstrip("+")
    if not number:
        log.warning("whatsapp.skipped", reason="empty phone number")
        return False

    body = _build_message(company_name, metrics, narrative_summary, narrative_actions)

    url = _API_URL.format(phone_number_id=settings.whatsapp_phone_number_id)
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, json=payload, headers=headers)
        success = resp.status_code == 200
        if success:
            log.info("whatsapp.sent", to=number[:6] + "****", company=company_name)
        else:
            log.warning(
                "whatsapp.api_error",
                status=resp.status_code,
                body=resp.text[:200],
            )
        return success
    except Exception as exc:
        log.error("whatsapp.failed", error=str(exc))
        return False
