"""Report retrieval, status polling, and PDF download."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.upload import ReportListItem, ReportOut


class SendEmailBody(BaseModel):
    extra_emails: list[EmailStr] = []

router = APIRouter(prefix="/reports", tags=["reports"])


def _check_access(report: Report, user: User) -> None:
    if user.role != "admin" and report.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("", response_model=list[ReportListItem])
def list_reports(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = select(Report).order_by(Report.period_year.desc(), Report.period_month.desc())
    if user.role != "admin":
        q = q.where(Report.company_id == user.company_id)
    reports = db.execute(q).scalars().all()
    return [ReportListItem.from_report(r) for r in reports]


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _check_access(report, user)
    return report


@router.get("/{report_id}/download")
def download_report(
    report_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _check_access(report, user)
    if not report.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not yet generated")
    pdf = Path(report.pdf_path)
    if not pdf.exists():
        raise HTTPException(status_code=404, detail="PDF file missing from storage")

    company_name = (
        report.company.name
        .lower()
        .replace(" ", "_")
        .replace("/", "_")[:30]
        if report.company
        else "report"
    )
    filename = f"ghostcfo_{company_name}_{report.period_year}-{report.period_month:02d}.pdf"
    return FileResponse(
        path=str(pdf),
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/{report_id}/status")
def report_status(
    report_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _check_access(report, user)
    return {
        "id": str(report.id),
        "generated": report.generated_at is not None,
        "pdf_ready": bool(report.pdf_path),
        "email_sent": report.email_sent,
        "health_score": report.metrics.get("health_score") if report.metrics else None,
        "health_rating": report.metrics.get("health_rating") if report.metrics else None,
    }


@router.get("/trends/revenue")
def revenue_trends(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Last 12 months of revenue + gross profit for the trend chart."""
    q = (
        select(Report)
        .order_by(Report.period_year.asc(), Report.period_month.asc())
    )
    if user.role != "admin":
        q = q.where(Report.company_id == user.company_id)

    reports = db.execute(q).scalars().all()
    result = []
    for r in reports:
        if not r.metrics:
            continue
        result.append({
            "period_month": r.period_month,
            "period_year": r.period_year,
            "revenue": r.metrics.get("revenue_current_month", 0),
            "gross_profit": r.metrics.get("gross_profit_current", 0),
        })
    return result[-12:]  # cap at 12 months


@router.post("/{report_id}/deliver", status_code=status.HTTP_202_ACCEPTED)
def resend_report(
    report_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: re-trigger delivery for a report (useful after fixing email/WhatsApp config)."""
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if not report.pdf_path:
        raise HTTPException(status_code=400, detail="PDF not yet generated — cannot deliver")
    from app.tasks.deliver_report import deliver_report_task
    deliver_report_task.delay(str(report_id))
    return {"status": "queued", "report_id": str(report_id)}


@router.post("/{report_id}/send-email")
def send_email_manual(
    report_id: uuid.UUID,
    body: SendEmailBody = Body(default_factory=SendEmailBody),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Send the report PDF by email. Optionally include extra recipients."""
    from datetime import datetime, timezone

    from app.reports.email import send_report_email

    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    _check_access(report, user)
    if not report.pdf_path:
        raise HTTPException(status_code=400, detail="PDF not yet generated")

    company = report.company
    if not company:
        raise HTTPException(status_code=400, detail="Company not found")

    recipient = company.owner_email or company.bookkeeper_email
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address configured for this company")

    narrative = {
        "summary": report.narrative_summary,
        "revenue": report.narrative_revenue,
        "costs": report.narrative_costs,
        "debtors": report.narrative_debtors,
        "payroll": report.narrative_payroll,
        "cash": report.narrative_cash,
        "actions": report.narrative_actions,
    }

    extra = [str(e) for e in body.extra_emails]
    ok = send_report_email(
        to_email=recipient,
        to_name=company.owner_name or company.name,
        company_name=company.trading_name or company.name,
        metrics=report.metrics or {},
        narrative=narrative,
        pdf_path=report.pdf_path,
        extra_to=extra,
    )

    if ok:
        report.email_sent = True
        report.email_sent_at = datetime.now(timezone.utc)
        db.commit()

    if not ok:
        raise HTTPException(status_code=502, detail="Email delivery failed — check server logs")

    all_to = [recipient] + extra
    return {"ok": True, "to": all_to}
