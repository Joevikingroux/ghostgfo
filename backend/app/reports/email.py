"""Email delivery via SendGrid — sends the monthly report PDF as an attachment."""
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
) -> bool:
    """Send the monthly report email. Returns True on success."""
    if not settings.sendgrid_api_key:
        log.warning("email.skipped", reason="SENDGRID_API_KEY not set")
        return False

    try:
        import sendgrid
        from sendgrid.helpers.mail import (
            Attachment,
            ContentId,
            Disposition,
            FileContent,
            FileName,
            FileType,
            Mail,
        )
    except ImportError:
        log.error("email.import_error", msg="sendgrid package not installed")
        return False

    month = metrics["period_month"]
    year = metrics["period_year"]
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

    subject = (
        f"Ghost CFO — {company_name} — {month_name} {year} Financial Report"
    )

    pdf_bytes = Path(pdf_path).read_bytes()
    encoded_pdf = base64.b64encode(pdf_bytes).decode()
    pdf_filename = f"ghostcfo_{company_name.lower().replace(' ', '_')[:30]}_{year}-{month:02d}.pdf"

    message = Mail(
        from_email=(settings.from_email, settings.from_name),
        to_emails=to_email,
        subject=subject,
        html_content=html_body,
    )
    message.attachment = Attachment(
        FileContent(encoded_pdf),
        FileName(pdf_filename),
        FileType("application/pdf"),
        Disposition("attachment"),
        ContentId("monthly_report"),
    )

    try:
        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        response = sg.send(message)
        success = response.status_code in {200, 201, 202}
        log.info(
            "email.sent",
            to=to_email,
            status=response.status_code,
            company=company_name,
        )
        return success
    except Exception as exc:
        log.error("email.failed", to=to_email, error=str(exc))
        return False
