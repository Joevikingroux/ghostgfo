"""File upload endpoint — Pastel Partner + Payroll exports."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.upload import Upload
from app.models.user import User
from app.schemas.upload import UploadOut

router = APIRouter(prefix="/uploads", tags=["uploads"])
log = get_logger(__name__)

_ALLOWED_TYPES = {
    "text/csv",
    "application/csv",
    "text/plain",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",  # some browsers send this for CSV
}
_ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx", ".txt"}
_MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB per file


def _delete_old_uploads(
    company_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: Session,
) -> None:
    """Delete files and DB records for any existing uploads for this company/period."""
    old = db.execute(
        select(Upload).where(
            Upload.company_id == company_id,
            Upload.period_month == period_month,
            Upload.period_year == period_year,
        )
    ).scalars().all()

    for upload in old:
        # Delete all individual files that were saved for this upload
        for field in (
            "income_statement_path", "balance_sheet_path", "debtors_age_path",
            "creditors_age_path", "payroll_summary_path",
            "payroll_employee_cost_path", "payroll_leave_path", "payroll_journal_path",
        ):
            path_str = getattr(upload, field, None)
            if path_str:
                try:
                    Path(path_str).unlink(missing_ok=True)
                except OSError:
                    pass
        db.delete(upload)

    # Remove the now-empty period directory if it exists
    period_dir = settings.upload_dir / str(company_id) / f"{period_year}-{period_month:02d}"
    if period_dir.exists():
        shutil.rmtree(period_dir, ignore_errors=True)

    if old:
        db.flush()
        log.info(
            "upload.cleanup",
            company_id=str(company_id),
            period=f"{period_year}-{period_month:02d}",
            deleted=len(old),
        )


def _save_upload(file: UploadFile, dest_dir: Path, prefix: str) -> str:
    """Validate, save, and return the file path."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{ext}' for {prefix}. Use CSV or Excel.",
        )
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}{ext}"
    dest = dest_dir / filename
    content = file.file.read()
    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"{prefix} file exceeds 20 MB limit",
        )
    dest.write_bytes(content)
    return str(dest)


@router.post("", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
def create_upload(
    period_month: int = Form(..., ge=1, le=12),
    period_year: int = Form(..., ge=2020, le=2099),
    income_statement: UploadFile | None = None,
    balance_sheet: UploadFile | None = None,
    debtors_age: UploadFile | None = None,
    creditors_age: UploadFile | None = None,
    payroll_summary: UploadFile | None = None,
    payroll_employee_cost: UploadFile | None = None,
    payroll_leave: UploadFile | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.company import Company

    if user.role not in {"bookkeeper", "owner", "admin"}:
        raise HTTPException(status_code=403, detail="Upload permission required")
    if not user.company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = db.get(Company, user.company_id)
    is_evolution = company and company.data_source == "evolution"

    # Remove any previous upload files/records for this period before saving new ones
    _delete_old_uploads(user.company_id, period_month, period_year, db)

    dest = settings.upload_dir / str(user.company_id) / f"{period_year}-{period_month:02d}"

    upload = Upload(
        company_id=user.company_id,
        uploaded_by=user.id,
        period_month=period_month,
        period_year=period_year,
        status="pending",
    )

    if is_evolution:
        # Evolution clients: accounting data is pushed automatically by the agent.
        # Only payroll files are uploaded here.
        if payroll_summary and payroll_summary.filename:
            upload.payroll_summary_path = _save_upload(payroll_summary, dest, "payroll_summary")
        if payroll_employee_cost and payroll_employee_cost.filename:
            upload.payroll_employee_cost_path = _save_upload(
                payroll_employee_cost, dest, "payroll_employee_cost"
            )
        if payroll_leave and payroll_leave.filename:
            upload.payroll_leave_path = _save_upload(payroll_leave, dest, "payroll_leave")

        db.add(upload)
        db.commit()
        db.refresh(upload)

        # If a report already exists for this period, apply payroll immediately.
        # Otherwise, save the files and let the agent include them when it next syncs.
        from app.models.report import Report
        existing_report = db.execute(
            select(Report).where(
                Report.company_id == user.company_id,
                Report.period_month == period_month,
                Report.period_year == period_year,
            )
        ).scalar_one_or_none()

        if existing_report:
            from app.tasks.generate_report import apply_payroll_to_report_task
            apply_payroll_to_report_task.delay(str(upload.id))
            log.info(
                "upload.evolution.payroll_queued",
                upload_id=str(upload.id),
                report_id=str(existing_report.id),
            )
        else:
            log.info(
                "upload.evolution.payroll_saved_awaiting_agent",
                upload_id=str(upload.id),
                company_id=str(user.company_id),
                period=f"{period_year}-{period_month:02d}",
            )

        return upload

    # --- Partner clients: all accounting files required ---
    if not income_statement or not balance_sheet or not debtors_age:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="income_statement, balance_sheet, and debtors_age are required.",
        )

    upload.income_statement_path = _save_upload(income_statement, dest, "income_statement")
    upload.balance_sheet_path = _save_upload(balance_sheet, dest, "balance_sheet")
    upload.debtors_age_path = _save_upload(debtors_age, dest, "debtors_age")

    if creditors_age and creditors_age.filename:
        upload.creditors_age_path = _save_upload(creditors_age, dest, "creditors_age")
    if payroll_summary and payroll_summary.filename:
        upload.payroll_summary_path = _save_upload(payroll_summary, dest, "payroll_summary")
    if payroll_employee_cost and payroll_employee_cost.filename:
        upload.payroll_employee_cost_path = _save_upload(
            payroll_employee_cost, dest, "payroll_employee_cost"
        )
    if payroll_leave and payroll_leave.filename:
        upload.payroll_leave_path = _save_upload(payroll_leave, dest, "payroll_leave")

    db.add(upload)
    db.commit()
    db.refresh(upload)

    log.info(
        "upload.created",
        upload_id=str(upload.id),
        company_id=str(user.company_id),
        period=f"{period_year}-{period_month:02d}",
    )

    from app.tasks.generate_report import generate_report_task
    generate_report_task.delay(str(upload.id))

    return upload


@router.get("", response_model=list[UploadOut])
def list_uploads(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import select
    q = select(Upload).order_by(Upload.created_at.desc())
    if user.role != "admin":
        q = q.where(Upload.company_id == user.company_id)
    return db.execute(q).scalars().all()


@router.get("/{upload_id}", response_model=UploadOut)
def get_upload(
    upload_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if user.role != "admin" and upload.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return upload
