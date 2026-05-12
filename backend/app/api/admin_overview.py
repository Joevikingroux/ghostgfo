"""Admin overview endpoint — aggregated stats for the operator dashboard."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.company import Company
from app.models.evolution_agent import EvolutionAgent  # noqa: F401 — required for joinedload
from app.models.report import Report
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

_PLAN_MRR = {"starter": 500, "professional": 900, "premium": 1500}


@router.get("/overview")
def admin_overview(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Single-call aggregated stats for the operator dashboard."""
    companies = db.execute(
        select(Company)
        .options(joinedload(Company.evolution_agent))
        .order_by(Company.name)
    ).unique().scalars().all()

    active = [c for c in companies if c.active]
    inactive = [c for c in companies if not c.active]

    mrr = sum(_PLAN_MRR.get(c.plan or "starter", 0) for c in active)
    plan_dist = dict(Counter(c.plan or "starter" for c in active))

    now = datetime.now(timezone.utc)
    payroll_pending_count = 0
    clients = []

    for company in active:
        report = db.execute(
            select(Report)
            .where(Report.company_id == company.id)
            .order_by(Report.period_year.desc(), Report.period_month.desc())
            .limit(1)
        ).scalars().first()

        agent = company.evolution_agent
        m = report.metrics or {} if report else {}

        if report and report.payroll_pending:
            payroll_pending_count += 1

        clients.append({
            "id": str(company.id),
            "name": company.trading_name or company.name,
            "plan": company.plan or "starter",
            "data_source": company.data_source or "partner",
            "health_score": m.get("health_score"),
            "health_rating": m.get("health_rating"),
            "last_report_month": report.period_month if report else None,
            "last_report_year": report.period_year if report else None,
            "last_report_generated": report.generated_at.isoformat() if report and report.generated_at else None,
            "payroll_pending": bool(report.payroll_pending) if report else False,
            "email_sent": bool(report.email_sent) if report else False,
            # Agent fields
            "agent_id": str(agent.id) if agent else None,
            "agent_last_heartbeat": agent.last_heartbeat_at.isoformat() if agent and agent.last_heartbeat_at else None,
            "agent_last_sync": agent.last_sync_at.isoformat() if agent and agent.last_sync_at else None,
            "agent_status": agent.last_sync_status if agent else None,
            "agent_active": bool(agent.active) if agent else False,
            "agent_server_name": agent.server_name if agent else None,
            "agent_db_name": agent.db_name if agent else None,
            "agent_sql_ok": agent.sql_connection_ok if agent else None,
            "agent_pending_sync_month": agent.pending_sync_month if agent else None,
            "agent_pending_sync_year": agent.pending_sync_year if agent else None,
        })

    health_dist = dict(Counter(
        c["health_rating"] for c in clients if c["health_rating"]
    ))

    reports_this_month = db.execute(
        select(Report).where(
            Report.period_month == now.month,
            Report.period_year == now.year,
        )
    ).scalars().all()

    recent_reports = db.execute(
        select(Report)
        .where(Report.generated_at.is_not(None))
        .order_by(Report.generated_at.desc())
        .limit(8)
    ).scalars().all()

    recent = []
    for r in recent_reports:
        if r.company:
            m = r.metrics or {}
            recent.append({
                "company_name": r.company.trading_name or r.company.name,
                "period_month": r.period_month,
                "period_year": r.period_year,
                "health_score": m.get("health_score"),
                "health_rating": m.get("health_rating"),
                "generated_at": r.generated_at.isoformat(),
                "email_sent": r.email_sent,
            })

    return {
        "mrr": mrr,
        "active_clients": len(active),
        "inactive_clients": len(inactive),
        "plans": plan_dist,
        "reports_this_month": len(reports_this_month),
        "payroll_pending_count": payroll_pending_count,
        "health_distribution": health_dist,
        "clients": clients,
        "recent_reports": recent,
        "fetched_at": now.isoformat(),
    }
