"""Cleanup task — delete orphaned pending companies after failed/abandoned signups."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.celery_app import celery
from app.core.logging import get_logger

log = get_logger(__name__)

_PENDING_TTL_HOURS = 2  # delete pending accounts older than this


@celery.task(name="ghostcfo.cleanup_pending", bind=True)
def cleanup_pending_task(self) -> dict:
    """Delete companies stuck in 'pending' state (signup started, payment never completed)."""
    from sqlalchemy import delete as sa_delete, select

    from app.core.database import SessionLocal
    from app.models.company import Company
    from app.models.user import User

    cutoff = datetime.now(timezone.utc) - timedelta(hours=_PENDING_TTL_HOURS)
    deleted = 0

    with SessionLocal() as db:
        stale = (
            db.execute(
                select(Company).where(
                    Company.subscription_status == "pending",
                    Company.active == False,  # noqa: E712
                    Company.created_at < cutoff,
                )
            )
            .scalars()
            .all()
        )

        for company in stale:
            cid = company.id
            db.execute(sa_delete(User).where(User.company_id == cid))
            db.delete(company)
            deleted += 1
            log.info("cleanup_pending.deleted company=%s name=%s", cid, company.name)

        if deleted:
            db.commit()

    log.info("cleanup_pending.done deleted=%d", deleted)
    return {"deleted": deleted}
