"""Weekly cash pulse task — sends a Monday morning email to Professional+ clients."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from app.core.celery_app import celery
from app.core.logging import get_logger

log = get_logger(__name__)

_SYNC_FRESH_HOURS = 2  # agent data is "fresh" if synced within this many hours


@celery.task(name="ghostcfo.weekly_pulse", bind=True, max_retries=2)
def weekly_pulse_task(self) -> dict:
    """Send a weekly cash pulse email to all active Professional+ companies."""
    from sqlalchemy import select

    from app.core.config import settings
    from app.core.database import SessionLocal
    from app.models.company import Company
    from app.models.evolution_agent import EvolutionAgent
    from app.models.report import Report
    from app.reports.email import send_weekly_pulse_email

    today = date.today()

    # -----------------------------------------------------------------------
    # Request fresh data from stale Evolution agents, retry if needed
    # -----------------------------------------------------------------------
    with SessionLocal() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=_SYNC_FRESH_HOURS)
        stale_agents = (
            db.execute(
                select(EvolutionAgent).where(
                    EvolutionAgent.active,
                    (EvolutionAgent.last_sync_at == None)  # noqa: E711
                    | (EvolutionAgent.last_sync_at < cutoff),
                )
            )
            .scalars()
            .all()
        )

        if stale_agents:
            stale_ids = [str(a.company_id) for a in stale_agents]
            for agent in stale_agents:
                agent.pending_sync_month = today.month
                agent.pending_sync_year = today.year
            db.commit()
            log.info(
                "weekly_pulse.sync_requested",
                companies=stale_ids,
                attempt=self.request.retries + 1,
            )
            try:
                raise self.retry(countdown=360)  # wait 6 min for agent to sync
            except self.MaxRetriesExceededError:
                from app.core.admin_notify import notify_admin

                notify_admin(
                    "weekly_pulse: agent sync timeout",
                    f"Evolution agents did not sync within the retry window.\n"
                    f"Company IDs with stale data: {', '.join(stale_ids)}\n"
                    f"Weekly pulse emails sent using most recent available data.",
                )

    # -----------------------------------------------------------------------
    # Send pulse emails
    # -----------------------------------------------------------------------
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

            report = db.execute(
                select(Report)
                .where(Report.company_id == company.id)
                .order_by(Report.period_year.desc(), Report.period_month.desc())
            ).scalar_one_or_none()

            if not report or not report.metrics:
                skipped += 1
                continue

            m = report.metrics
            ok = send_weekly_pulse_email(
                to_email=recipient,
                to_name=company.owner_name or company.name,
                company_name=company.trading_name or company.name,
                cash_balance=m.get("cash_balance", 0.0),
                cash_runway_weeks=m.get("cash_runway_weeks", 0.0),
                revenue_current=m.get("revenue_current_month", 0.0),
                revenue_change_pct=m.get("revenue_change_pct", 0.0),
                overdue_count=m.get("overdue_invoices_count", 0),
                overdue_value=m.get("overdue_invoices_value", 0.0),
                period_month=report.period_month,
                period_year=report.period_year,
                portal_url=settings.base_url,
            )
            if ok:
                sent += 1
                log.info("weekly_pulse.sent", company=company.name)
            else:
                skipped += 1

    log.info("weekly_pulse.done", sent=sent, skipped=skipped)
    return {"sent": sent, "skipped": skipped}
