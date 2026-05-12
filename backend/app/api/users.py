"""User management endpoints."""
from __future__ import annotations

import secrets
import string
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import hash_password
from app.models.company import Company
from app.models.user import User
from app.schemas.user import UserAdminOut, UserCreate, UserOut, UserUpdate


def _generate_temp_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(14))

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

    temp_pw = body.password or _generate_temp_password()
    new_user = User(
        email=body.email,
        password_hash=hash_password(temp_pw),
        full_name=body.full_name,
        role=body.role,
        company_id=body.company_id,
        must_change_password=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    from app.reports.email import send_temp_password_email
    send_temp_password_email(
        to_email=new_user.email,
        to_name=new_user.full_name or new_user.email,
        temp_password=temp_pw,
    )

    return new_user


@router.get("/me", response_model=UserOut)
def my_profile(user: User = Depends(get_current_user)):
    return user


@router.patch("/{user_id}", response_model=UserAdminOut)
def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    caller: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email is not None:
        conflict = db.execute(
            select(User).where(User.email == body.email, User.id != user_id)
        ).scalar_one_or_none()
        if conflict:
            raise HTTPException(status_code=409, detail="Email already in use")
        target.email = body.email

    if body.full_name is not None:
        target.full_name = body.full_name or None
    if body.role is not None:
        target.role = body.role
    if body.company_id is not None:
        target.company_id = body.company_id
    if body.active is not None:
        if not body.active and str(target.id) == str(caller.id):
            raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
        target.active = body.active

    db.commit()
    db.refresh(target)

    # Reload with company relationship for response
    db.expire(target)
    target = db.execute(
        select(User).options(joinedload(User.company)).where(User.id == user_id)
    ).scalar_one()

    return UserAdminOut(
        id=target.id,
        email=target.email,
        full_name=target.full_name,
        role=target.role,
        company_id=target.company_id,
        company_name=target.company.name if target.company else None,
        active=target.active,
        must_change_password=target.must_change_password,
        totp_enabled=target.totp_enabled,
    )


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


@router.post("/{user_id}/reset-password")
def admin_reset_password(
    user_id: uuid.UUID,
    caller: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Admin: generate a new temp password, email it, and force password change on next login."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role == "admin":
        raise HTTPException(status_code=403, detail="Cannot reset password for admin users")
    if str(target.id) == str(caller.id):
        raise HTTPException(status_code=400, detail="Use the change-password flow to update your own password")

    temp_pw = _generate_temp_password()
    target.password_hash = hash_password(temp_pw)
    target.must_change_password = True
    db.commit()

    from app.reports.email import send_temp_password_email
    sent = send_temp_password_email(
        to_email=target.email,
        to_name=target.full_name or target.email,
        temp_password=temp_pw,
    )

    return {"ok": True, "email_sent": sent}


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
