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
    from app.reports.telegram import send_telegram_message

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

        results = {"email": False, "telegram": False}

        # --- Email ---
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
            log.info(
                "deliver.email_skipped",
                report_id=report_id,
                reason="no email or no PDF",
            )

        # --- Telegram ---
        telegram_chat_id = company.owner_telegram
        if telegram_chat_id:
            try:
                ok = send_telegram_message(
                    chat_id=telegram_chat_id,
                    company_name=company.trading_name or company.name,
                    metrics=metrics,
                    narrative_summary=report.narrative_summary,
                    narrative_actions=report.narrative_actions,
                )
                results["telegram"] = ok
                if ok:
                    report.telegram_sent = True
                    report.telegram_sent_at = datetime.now(timezone.utc)
                    db.commit()
                    log.info("deliver.telegram_ok", report_id=report_id)
            except Exception as exc:
                log.error("deliver.telegram_error", report_id=report_id, error=str(exc))
        else:
            log.info(
                "deliver.telegram_skipped",
                report_id=report_id,
                reason="no Telegram chat ID",
            )

        # Retry if both channels failed (transient network issue possible)
        if not results["email"] and not results["telegram"]:
            if recipient_email or telegram_chat_id:
                raise self.retry(
                    exc=RuntimeError("Both delivery channels failed"),
                    countdown=60 * (2 ** self.request.retries),
                )

        return results
    finally:
        db.close()
