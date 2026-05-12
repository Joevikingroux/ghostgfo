"""Email delivery via Resend (resend.com) — sends the monthly report PDF as an attachment."""
from __future__ import annotations

import base64
import calendar
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=True)


def _currency(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"R {value / 1_000_000:.2f}m"
    return f"R {round(value):,}"


_jinja.filters["currency"] = _currency


def send_report_email(
    *,
    to_email: str,
    to_name: str,
    company_name: str,
    metrics: dict[str, Any],
    narrative: dict[str, str],
    pdf_path: str | Path,
    extra_to: list[str] | None = None,
) -> bool:
    """Send the monthly report email via Resend. Returns True on success."""
    if not settings.resend_api_key:
        log.warning("email.skipped", reason="RESEND_API_KEY not set")
        return False

    try:
        import resend
    except ImportError:
        log.error("email.import_error", msg="resend package not installed — run: pip install resend")
        return False

    resend.api_key = settings.resend_api_key

    month = metrics.get("period_month", 1)
    year = metrics.get("period_year", 2025)
    month_name = calendar.month_name[month]

    html_body = _jinja.get_template("email_report.html").render(
        company_name=company_name,
        month_name=month_name,
        year=year,
        health_score=metrics.get("health_score", 0),
        health_rating=metrics.get("health_rating", "fair"),
        health_flags=metrics.get("health_flags", []),
        revenue_current=metrics.get("revenue_current_month", 0),
        revenue_change_pct=metrics.get("revenue_change_pct", 0),
        gross_margin_pct=metrics.get("gross_margin_pct", 0),
        gross_margin_trend=metrics.get("gross_margin_trend", ""),
        cash_balance=metrics.get("cash_balance", 0),
        cash_runway_weeks=metrics.get("cash_runway_weeks", 0),
        payroll_gross=metrics.get("payroll_gross_total", 0),
        payroll_change_pct=metrics.get("payroll_change_pct", 0),
        payroll_pct_of_revenue=metrics.get("payroll_pct_of_revenue", 0),
        leave_liability=metrics.get("leave_liability_rand", 0),
        leave_weeks=metrics.get("leave_liability_weeks_payroll", 0),
        sections=[
            ("Revenue", narrative.get("revenue")),
            ("Costs", narrative.get("costs")),
            ("Customers (Debtors)", narrative.get("debtors")),
            ("Payroll & Staff Costs", narrative.get("payroll") if metrics.get("payroll_gross_total") else None),
            ("Cash Position", narrative.get("cash")),
        ],
        narrative_actions=narrative.get("actions"),
        narrative_summary=narrative.get("summary"),
        portal_url=settings.base_url,
        brand_footer=settings.brand_footer,
    )

    subject = f"Ghost CFO — {company_name} — {month_name} {year} Financial Report"

    pdf_bytes = Path(pdf_path).read_bytes()
    pdf_filename = f"ghostcfo_{company_name.lower().replace(' ', '_')[:30]}_{year}-{month:02d}.pdf"

    all_to = [to_email] + (extra_to or [])
    try:
        response = resend.Emails.send({
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": all_to,
            "subject": subject,
            "html": html_body,
            "attachments": [
                {
                    "filename": pdf_filename,
                    "content": base64.b64encode(pdf_bytes).decode(),
                }
            ],
        })
        log.info("email.sent", to=all_to, id=response.get("id"), company=company_name)
        return True
    except Exception as exc:
        log.error("email.failed", to=all_to, error=str(exc))
        return False


def send_payroll_reminder_email(
    *,
    to_email: str,
    to_name: str,
    company_name: str,
    period_month: int,
    period_year: int,
    portal_url: str,
) -> bool:
    """Notify the bookkeeper that Evolution data is ready and payroll needs uploading."""
    if not settings.resend_api_key:
        log.warning("email.skipped", reason="RESEND_API_KEY not set")
        return False
    try:
        import resend
    except ImportError:
        log.error("email.import_error", msg="resend package not installed")
        return False

    resend.api_key = settings.resend_api_key
    month_name = calendar.month_name[period_month]
    html_body = _jinja.get_template("email_payroll_reminder.html").render(
        to_name=to_name,
        company_name=company_name,
        month_name=month_name,
        period_year=period_year,
        portal_url=portal_url,
    )
    subject = f"Ghost CFO — {company_name} — Upload Payroll to Complete {month_name} {period_year} Report"
    try:
        response = resend.Emails.send({
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        })
        log.info("payroll_reminder.sent", to=to_email, id=response.get("id"), company=company_name)
        return True
    except Exception as exc:
        log.error("payroll_reminder.failed", to=to_email, error=str(exc))
        return False


def send_debtor_alert_email(
    *,
    to_email: str,
    to_name: str,
    company_name: str,
    overdue_count: int,
    overdue_value: float,
    debtor_days: float,
    portal_url: str,
) -> bool:
    """Send a debtor overdue alert email (Professional+)."""
    if not settings.resend_api_key:
        log.warning("email.skipped", reason="RESEND_API_KEY not set")
        return False
    try:
        import resend
    except ImportError:
        log.error("email.import_error", msg="resend package not installed")
        return False

    resend.api_key = settings.resend_api_key
    html_body = _jinja.get_template("email_debtor_alert.html").render(
        to_name=to_name,
        company_name=company_name,
        overdue_count=overdue_count,
        overdue_value=_currency(overdue_value),
        debtor_days=round(debtor_days),
        portal_url=portal_url,
    )
    subject = f"Ghost CFO — {company_name} — Overdue Invoice Alert"
    try:
        response = resend.Emails.send({
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        })
        log.info("debtor_alert.sent", to=to_email, id=response.get("id"), company=company_name)
        return True
    except Exception as exc:
        log.error("debtor_alert.failed", to=to_email, error=str(exc))
        return False


def send_weekly_pulse_email(
    *,
    to_email: str,
    to_name: str,
    company_name: str,
    cash_balance: float,
    cash_runway_weeks: float,
    revenue_current: float,
    revenue_change_pct: float,
    overdue_count: int,
    overdue_value: float,
    period_month: int,
    period_year: int,
    portal_url: str,
) -> bool:
    """Send a weekly cash pulse email (Professional+)."""
    if not settings.resend_api_key:
        log.warning("email.skipped", reason="RESEND_API_KEY not set")
        return False
    try:
        import resend
    except ImportError:
        log.error("email.import_error", msg="resend package not installed")
        return False

    resend.api_key = settings.resend_api_key
    month_name = calendar.month_name[period_month]
    html_body = _jinja.get_template("email_weekly_pulse.html").render(
        to_name=to_name,
        company_name=company_name,
        cash_balance=_currency(cash_balance),
        cash_runway_weeks=round(cash_runway_weeks, 1),
        revenue_current=_currency(revenue_current),
        revenue_change_pct=revenue_change_pct,
        overdue_count=overdue_count,
        overdue_value=_currency(overdue_value),
        month_name=month_name,
        period_year=period_year,
        portal_url=portal_url,
    )
    subject = f"Ghost CFO — {company_name} — Weekly Cash Pulse"
    try:
        response = resend.Emails.send({
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        })
        log.info("weekly_pulse.sent", to=to_email, id=response.get("id"), company=company_name)
        return True
    except Exception as exc:
        log.error("weekly_pulse.failed", to=to_email, error=str(exc))
        return False


def send_temp_password_email(
    *,
    to_email: str,
    to_name: str,
    temp_password: str,
) -> bool:
    """Send an admin-generated temporary password to a user."""
    if not settings.resend_api_key:
        log.warning("email.skipped", reason="RESEND_API_KEY not set")
        return False
    try:
        import resend
    except ImportError:
        log.error("email.import_error", msg="resend package not installed")
        return False

    resend.api_key = settings.resend_api_key
    login_url = f"{settings.base_url}/login"
    html_body = (
        f"<p>Hi {to_name},</p>"
        f"<p>An administrator has reset your Ghost CFO password.</p>"
        f"<p>Your temporary password is: <strong style='font-family:monospace;font-size:16px'>{temp_password}</strong></p>"
        f"<p>You will be required to set a new password when you log in.</p>"
        f"<p><a href='{login_url}'>Log in to Ghost CFO</a></p>"
        f"<p style='color:#888;font-size:12px'>Ghost CFO — powered by Numbers10 Technology Solutions</p>"
    )
    try:
        response = resend.Emails.send({
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": [to_email],
            "subject": "Ghost CFO — your temporary password",
            "html": html_body,
        })
        log.info("temp_password.sent", to=to_email, id=response.get("id"))
        return True
    except Exception as exc:
        log.error("temp_password.failed", to=to_email, error=str(exc))
        return False


def send_welcome_email(
    *,
    to_email: str,
    to_name: str,
    company_name: str,
    reset_link: str,
) -> bool:
    """Send a bookkeeper welcome email with a set-password link."""
    return _send_auth_email(
        to_email=to_email,
        to_name=to_name,
        company_name=company_name,
        reset_link=reset_link,
        is_reset=False,
        subject=f"Ghost CFO — your bookkeeper account for {company_name}",
    )


def send_password_reset_email(
    *,
    to_email: str,
    to_name: str,
    reset_link: str,
) -> bool:
    """Send a password-reset email."""
    return _send_auth_email(
        to_email=to_email,
        to_name=to_name,
        company_name="",
        reset_link=reset_link,
        is_reset=True,
        subject="Ghost CFO — reset your password",
    )


def _send_auth_email(
    *,
    to_email: str,
    to_name: str,
    company_name: str,
    reset_link: str,
    is_reset: bool,
    subject: str,
) -> bool:
    if not settings.resend_api_key:
        log.warning("email.skipped", reason="RESEND_API_KEY not set")
        return False

    try:
        import resend
    except ImportError:
        log.error("email.import_error", msg="resend package not installed")
        return False

    resend.api_key = settings.resend_api_key

    html_body = _jinja.get_template("email_welcome.html").render(
        to_name=to_name,
        to_email=to_email,
        company_name=company_name,
        reset_link=reset_link,
        is_reset=is_reset,
    )

    try:
        response = resend.Emails.send({
            "from": f"{settings.from_name} <{settings.from_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        })
        log.info("auth_email.sent", to=to_email, id=response.get("id"))
        return True
    except Exception as exc:
        log.error("auth_email.failed", to=to_email, error=str(exc))
        return False
