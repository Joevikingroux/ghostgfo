"""Debtor alert task — emails Professional+ clients when invoices are 60+ days overdue."""

from __future__ import annotations

from app.core.celery_app import celery
from app.core.logging import get_logger

log = get_logger(__name__)

_OVERDUE_THRESHOLD = 61  # days — flag invoices past this age


@celery.task(name="ghostcfo.debtor_alerts", bind=True, max_retries=2)
def debtor_alerts_task(self) -> dict:
    """Check all Professional+ companies for overdue debtors and send alert emails."""
    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.company import Company
    from app.models.report import Report
    from app.reports.email import send_debtor_alert_email
    from app.core.config import settings

    sent = 0
    skipped = 0

    with SessionLocal() as db:
        companies = (
            db.execute(
                select(Company).where(
                    Company.active,
                    Company.plan.in_(["professional", "premium"]),
                )
            )
            .scalars()
            .all()
        )

        for company in companies:
            recipient = company.owner_email or company.bookkeeper_email
            if not recipient:
                skipped += 1
                continue

            # Find the most recent report for this company
            report = db.execute(
                select(Report)
                .where(Report.company_id == company.id)
                .order_by(Report.period_year.desc(), Report.period_month.desc())
            ).scalar_one_or_none()

            if not report or not report.metrics:
                skipped += 1
                continue

            m = report.metrics
            overdue_count = m.get("overdue_invoices_count", 0)
            overdue_value = m.get("overdue_invoices_value", 0.0)

            if overdue_count == 0:
                skipped += 1
                continue

            ok = send_debtor_alert_email(
                to_email=recipient,
                to_name=company.owner_name or company.name,
                company_name=company.trading_name or company.name,
                overdue_count=overdue_count,
                overdue_value=overdue_value,
                debtor_days=m.get("debtor_days", 0.0),
                portal_url=settings.base_url,
            )
            if ok:
                sent += 1
                log.info(
                    "debtor_alerts.sent",
                    company=company.name,
                    overdue_count=overdue_count,
                )
            else:
                skipped += 1

    log.info("debtor_alerts.done", sent=sent, skipped=skipped)
    return {"sent": sent, "skipped": skipped}
