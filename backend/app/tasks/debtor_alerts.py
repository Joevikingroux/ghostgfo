"""Debtor alert task — runs daily, fires WhatsApp when invoices cross the 61-day mark.

For each active Professional/Premium company with a WhatsApp number:
1. Look at the latest report's metrics.
2. If there are invoices aged 61–90 or 90+ days that weren't flagged today,
   send a short WhatsApp alert to the business owner.

"New crossing" detection: we compare the worst_offenders list against the names
stored in the previous alert (persisted inside the report metrics JSONB). An
invoice is considered new if it appears with a worse bucket than last seen.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.celery_app import celery

log = logging.getLogger(__name__)


def _overdue_text(company_name: str, offenders: list[dict]) -> str:
    lines = [
        "*Ghost CFO — Debtor Alert*",
        f"_{company_name}_",
        "",
        f"⚠️  {len(offenders)} customer(s) now overdue 61+ days:",
        "",
    ]
    for o in offenders[:5]:
        lines.append(
            f"• {o['name']} — R{int(o['overdue_value']):,} ({o['worst_bucket']})"
        )
    lines += [
        "",
        "Call these customers today before the balance grows further.",
        "_Reply STOP to unsubscribe from alerts._",
    ]
    return "\n".join(lines)[:1024]


@celery.task(name="ghostcfo.debtor_alerts", bind=True, max_retries=1)
def debtor_alerts_task(self) -> dict:
    from sqlalchemy import select
    from app.core.database import SessionLocal
    from app.models.company import Company
    from app.models.report import Report
    from app.reports.whatsapp import send_whatsapp_message

    db = SessionLocal()
    sent = 0
    skipped = 0
    try:
        companies = db.execute(
            select(Company).where(
                Company.active == True,  # noqa: E712
                Company.plan.in_(["professional", "premium"]),
                Company.owner_whatsapp != None,  # noqa: E711
            )
        ).scalars().all()

        for company in companies:
            report = db.execute(
                select(Report)
                .where(Report.company_id == company.id)
                .order_by(Report.period_year.desc(), Report.period_month.desc())
            ).scalar_one_or_none()

            if not report or not report.metrics:
                skipped += 1
                continue

            offenders: list[dict] = report.metrics.get("worst_offenders", [])
            critical = [o for o in offenders if o.get("worst_bucket") in ("61-90", "90+")]
            if not critical:
                skipped += 1
                continue

            # Skip if we already sent this exact set today
            alert_state = report.metrics.get("_last_debtor_alert") or {}
            today = datetime.now(timezone.utc).date().isoformat()
            last_alert_date = alert_state.get("date", "")
            last_names = set(alert_state.get("names", []))
            current_names = {o["name"] for o in critical}

            if last_alert_date == today and current_names == last_names:
                skipped += 1
                continue

            ok = send_whatsapp_message(
                to_number=company.owner_whatsapp,
                company_name=company.name,
                metrics=report.metrics,
                narrative_summary=_overdue_text(company.name, critical),
                narrative_actions=None,
            )
            if ok:
                updated = dict(report.metrics)
                updated["_last_debtor_alert"] = {
                    "date": today,
                    "names": list(current_names),
                }
                report.metrics = updated
                db.commit()
                sent += 1
                log.info(
                    "debtor_alert.sent company=%s overdue_count=%d",
                    company.name, len(critical),
                )
            else:
                skipped += 1

        return {"sent": sent, "skipped": skipped}
    except Exception as exc:
        log.exception("debtor_alerts.failed: %s", exc)
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()
