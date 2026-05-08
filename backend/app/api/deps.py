"""Shared FastAPI dependencies."""
from __future__ import annotations

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User


def _extract_token(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> str:
    """Accept token from Authorization: Bearer header OR httpOnly cookie."""
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:]
    if access_token:
        return access_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def require_company_access(
    company_id: str,
    user: User = Depends(get_current_user),
) -> User:
    """Allows admins to access any company; others only their own."""
    if user.role == "admin":
        return user
    if str(user.company_id) != company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return user
