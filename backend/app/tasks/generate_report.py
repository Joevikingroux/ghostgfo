"""Celery task: end-to-end monthly report generation, then delivery."""
from __future__ import annotations

import uuid
from typing import Any

from app.core.celery_app import celery
from app.core.logging import get_logger

log = get_logger(__name__)


@celery.task(name="ghostcfo.generate_report", bind=True, max_retries=2)
def generate_report_task(self, upload_id: str) -> str:
    from app.core.database import SessionLocal
    from app.pipeline import run_for_upload
    from app.tasks.deliver_report import deliver_report_task

    db = SessionLocal()
    try:
        report = run_for_upload(uuid.UUID(upload_id), db)
        report_id = str(report.id)
        # Chain delivery — runs in a separate worker slot so generation
        # is not blocked and delivery can be retried independently.
        deliver_report_task.delay(report_id)
        return report_id
    except Exception as exc:
        log.error("task.generate_report.failed", upload_id=upload_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery.task(name="ghostcfo.generate_report_from_agent", bind=True, max_retries=2)
def generate_report_from_agent(
    self,
    company_id: str,
    metrics_data: dict[str, Any],
    period_month: int,
    period_year: int,
) -> str:
    """Generate a report from an Evolution agent snapshot (no Upload row required)."""
    from app.core.database import SessionLocal
    from app.pipeline import run_for_agent_data
    from app.tasks.deliver_report import deliver_report_task

    db = SessionLocal()
    try:
        report = run_for_agent_data(
            company_id=uuid.UUID(company_id),
            metrics_data=metrics_data,
            period_month=period_month,
            period_year=period_year,
            db=db,
        )
        report_id = str(report.id)
        deliver_report_task.delay(report_id)
        return report_id
    except Exception as exc:
        log.error(
            "task.generate_report_from_agent.failed",
            company_id=company_id,
            period=f"{period_month}/{period_year}",
            error=str(exc),
        )
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
