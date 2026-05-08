"""Auth endpoints: login, refresh, logout, me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserMe

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_NAME = "access_token"
_COOKIE_MAX_AGE = 60 * 60 * 24  # 24 hours


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.email == body.email, User.active == True)  # noqa: E712
    ).scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(
        str(user.id),
        extra={"role": user.role, "company_id": str(user.company_id)},
    )

    # Set httpOnly cookie for browser clients
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # set True behind HTTPS in production
        max_age=_COOKIE_MAX_AGE,
    )
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(_COOKIE_NAME)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserMe)
def me(user: User = Depends(get_current_user)):
    return UserMe(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        company_id=str(user.company_id) if user.company_id else None,
    )
