"""Company management endpoints (admin only for create/delete)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


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
