"""Celery task: deliver a generated report by email and WhatsApp.

Called automatically after report generation, and available for manual
re-trigger via the admin API.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.celery_app import celery
from app.core.logging import get_logger

log = get_logger(__name__)


@celery.task(
    name="ghostcfo.deliver_report",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 min initial, doubles each retry
)
def deliver_report_task(self, report_id: str) -> dict:
    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.report import Report
    from app.reports.email import send_report_email

    db = SessionLocal()
    try:
        report = db.get(Report, uuid.UUID(report_id))
        if not report:
            log.error("deliver.report_not_found", report_id=report_id)
            return {"status": "error", "reason": "report not found"}

        company = report.company
        if not company:
            log.error("deliver.company_not_found", report_id=report_id)
            return {"status": "error", "reason": "company not found"}

        # Evolution report waiting for payroll: send reminder to bookkeeper, not full report to owner
        if report.payroll_pending:
            from app.reports.email import send_payroll_reminder_email
            from app.core.config import settings

            reminder_to = company.bookkeeper_email or company.owner_email
            if reminder_to:
                ok = send_payroll_reminder_email(
                    to_email=reminder_to,
                    to_name=company.bookkeeper_name or company.owner_name or company.name,
                    company_name=company.trading_name or company.name,
                    period_month=report.period_month,
                    period_year=report.period_year,
                    portal_url=settings.base_url,
                )
                log.info(
                    "deliver.payroll_reminder_sent" if ok else "deliver.payroll_reminder_failed",
                    report_id=report_id,
                    to=reminder_to,
                )
            return {"payroll_pending": True, "reminder_sent": bool(reminder_to)}

        # Full report: send to owner (or bookkeeper as fallback)
        metrics = report.metrics or {}
        narrative = {
            "summary": report.narrative_summary,
            "revenue": report.narrative_revenue,
            "costs": report.narrative_costs,
            "debtors": report.narrative_debtors,
            "payroll": report.narrative_payroll,
            "cash": report.narrative_cash,
            "actions": report.narrative_actions,
        }

        results = {"email": False}
        recipient_email = company.owner_email or company.bookkeeper_email
        if recipient_email and report.pdf_path:
            try:
                ok = send_report_email(
                    to_email=recipient_email,
                    to_name=company.owner_name or company.name,
                    company_name=company.trading_name or company.name,
                    metrics=metrics,
                    narrative=narrative,
                    pdf_path=report.pdf_path,
                )
                results["email"] = ok
                if ok:
                    report.email_sent = True
                    report.email_sent_at = datetime.now(timezone.utc)
                    db.commit()
                    log.info("deliver.email_ok", report_id=report_id, to=recipient_email)
            except Exception as exc:
                log.error("deliver.email_error", report_id=report_id, error=str(exc))
        else:
            log.info("deliver.email_skipped", report_id=report_id, reason="no email or no PDF")

        if not results["email"] and recipient_email:
            raise self.retry(
                exc=RuntimeError("Email delivery failed"),
                countdown=60 * (2 ** self.request.retries),
            )

        return results
    finally:
        db.close()
