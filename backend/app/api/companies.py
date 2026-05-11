"""Company management endpoints (admin only for create/delete)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import generate_reset_token, hash_password
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])
log = get_logger(__name__)


def _provision_bookkeeper(
    db: Session,
    company: Company,
    bookkeeper_email: str,
    bookkeeper_name: str,
) -> None:
    """Create a bookkeeper user and send them a welcome / set-password email."""
    if not bookkeeper_email:
        return

    existing = db.execute(
        select(User).where(User.email == bookkeeper_email)
    ).scalar_one_or_none()

    if existing:
        # Already has an account — just make sure they're linked to this company
        if not existing.company_id:
            existing.company_id = company.id
            db.commit()
        return

    from app.reports.email import send_welcome_email

    token = generate_reset_token()
    new_user = User(
        email=bookkeeper_email,
        password_hash=hash_password(token),  # placeholder — overwritten on first login
        full_name=bookkeeper_name or None,
        role="bookkeeper",
        company_id=company.id,
        active=True,
        must_change_password=True,
        password_reset_token=token,
        password_reset_expires=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(new_user)
    db.commit()

    reset_url = f"{settings.base_url}/set-password?token={token}"
    send_welcome_email(
        to_email=bookkeeper_email,
        to_name=bookkeeper_name or "",
        company_name=company.name,
        reset_link=reset_url,
    )
    log.info("bookkeeper.provisioned", email=bookkeeper_email, company_id=str(company.id))


@router.get("", response_model=list[CompanyOut])
def list_companies(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(select(Company).order_by(Company.name)).scalars().all()
    return rows


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    body: CompanyCreate,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    company = Company(**body.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)

    if body.bookkeeper_email:
        _provision_bookkeeper(db, company, body.bookkeeper_email, body.bookkeeper_name or "")

    return company


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if user.role != "admin" and user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return company


@router.patch("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: uuid.UUID,
    body: CompanyUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Non-admins can only update their own company, and cannot change plan/active/data_source
    if user.role != "admin":
        if user.company_id != company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        restricted = body.model_dump(exclude_none=True)
        for f in ("plan", "active"):
            restricted.pop(f, None)
        for field, value in restricted.items():
            setattr(company, field, value)
    else:
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(company, field, value)

    db.commit()
    db.refresh(company)

    # Provision bookkeeper if email was set or changed
    bk_email = body.bookkeeper_email or company.bookkeeper_email
    bk_name = body.bookkeeper_name or company.bookkeeper_name or ""
    if bk_email:
        _provision_bookkeeper(db, company, bk_email, bk_name)

    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: uuid.UUID,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
