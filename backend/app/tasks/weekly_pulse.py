"""Weekly cash pulse — Monday morning WhatsApp to Professional/Premium clients.

Sends a short 3-bullet cash position update so the business owner starts
the week knowing their cash balance, runway, and biggest upcoming risk.
"""
from __future__ import annotations

import calendar
import logging

from app.core.celery_app import celery

log = logging.getLogger(__name__)


def _pulse_text(company_name: str, metrics: dict) -> str:
    month = metrics.get("period_month", 0)
    year = metrics.get("period_year", "")
    month_name = calendar.month_name[int(month)] if str(month).isdigit() else ""

    cash = metrics.get("cash_balance", 0)
    runway = metrics.get("cash_runway_weeks", 0)
    rev = metrics.get("revenue_current_month", 0)
    overdue_val = metrics.get("overdue_invoices_value", 0)
    overdue_count = metrics.get("overdue_invoices_count", 0)
    payroll = metrics.get("payroll_gross_total", 0)
    cash_covers = metrics.get("cash_covers_payroll", True)
    score = metrics.get("health_score", "—")
    rating = (metrics.get("health_rating") or "").capitalize()

    lines = [
        f"*Ghost CFO — Weekly Pulse* 📊",
        f"_{company_name} · {month_name} {year}_",
        "",
        f"💵 Cash balance: R{int(cash):,} ({runway:.1f} weeks runway)",
        f"📈 Revenue ({month_name}): R{int(rev):,}",
    ]

    if overdue_count:
        lines.append(
            f"⚠️  Overdue receivables: R{int(overdue_val):,} "
            f"({overdue_count} invoice{'s' if overdue_count != 1 else ''})"
        )

    if payroll:
        if not cash_covers:
            lines.append(f"🔴 Cash may not cover next payroll (R{int(payroll):,}) — act now!")
        else:
            lines.append(f"✅ Cash covers next payroll run (R{int(payroll):,})")

    lines += [
        "",
        f"Health score: {score}/100 — {rating}",
        "",
        "_Have a great week. Full report on ghostcfo.numbers10.co.za_",
    ]

    return "\n".join(lines)[:1024]


@celery.task(name="ghostcfo.weekly_pulse", bind=True, max_retries=1)
def weekly_pulse_task(self) -> dict:
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

            pulse = _pulse_text(company.name, report.metrics)
            ok = send_whatsapp_message(
                to_number=company.owner_whatsapp,
                company_name=company.name,
                metrics=report.metrics,
                narrative_summary=pulse,
                narrative_actions=None,
            )
            if ok:
                sent += 1
                log.info("weekly_pulse.sent company=%s", company.name)
            else:
                skipped += 1

        return {"sent": sent, "skipped": skipped}
    except Exception as exc:
        log.exception("weekly_pulse.failed: %s", exc)
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()
