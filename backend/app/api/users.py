"""User management endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models.company import Company
from app.models.user import User
from app.schemas.user import UserAdminOut, UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserAdminOut])
def list_users(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = (
        db.execute(
            select(User)
            .options(joinedload(User.company))
            .order_by(User.email)
        )
        .scalars()
        .all()
    )
    result = []
    for u in rows:
        result.append(
            UserAdminOut(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                company_id=u.company_id,
                company_name=u.company.name if u.company else None,
                active=u.active,
                must_change_password=u.must_change_password,
                totp_enabled=u.totp_enabled,
            )
        )
    return result


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    existing = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    new_user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        company_id=body.company_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me", response_model=UserOut)
def my_profile(user: User = Depends(get_current_user)):
    return user


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: uuid.UUID,
    caller: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if str(target.id) == str(caller.id):
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    target.active = False
    db.commit()
    db.refresh(target)
    return target


@router.patch("/{user_id}/activate", response_model=UserOut)
def activate_user(
    user_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.active = True
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    caller: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if str(target.id) == str(caller.id):
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.delete(target)
    db.commit()
