"""Auth endpoints: login, 2FA, password reset, logout, me."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_partial_token,
    decode_token,
    generate_reset_token,
    generate_totp_secret,
    hash_password,
    make_totp_qr_image,
    make_totp_qr_uri,
    verify_password,
    verify_totp,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    Disable2FARequest,
    LoginRequest,
    ResetPasswordConfirm,
    ResetPasswordRequest,
    TokenResponse,
    TwoFAConfirmRequest,
    TwoFASetupResponse,
    TwoFAVerifyRequest,
    UserMe,
)

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger(__name__)

_COOKIE_NAME = "access_token"
_COOKIE_MAX_AGE = 60 * 60 * 24  # 24 hours


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=_COOKIE_MAX_AGE,
    )


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------


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

    if user.totp_enabled:
        partial = create_partial_token(str(user.id))
        return TokenResponse(requires_2fa=True, partial_token=partial, access_token="")

    token = create_access_token(
        str(user.id), extra={"role": user.role, "company_id": str(user.company_id)}
    )
    _set_auth_cookie(response, token)
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
        must_change_password=user.must_change_password,
        totp_enabled=user.totp_enabled,
    )


# ---------------------------------------------------------------------------
# 2FA flow
# ---------------------------------------------------------------------------


@router.post("/2fa/verify", response_model=TokenResponse)
def verify_2fa(
    body: TwoFAVerifyRequest, response: Response, db: Session = Depends(get_db)
):
    try:
        payload = decode_token(body.partial_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired 2FA session")

    if payload.get("type") != "partial":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user = db.get(User, uuid.UUID(payload["sub"]))
    if not user or not user.active or not user.totp_enabled or not user.totp_secret:
        raise HTTPException(status_code=401, detail="Invalid 2FA session")

    if not verify_totp(user.totp_secret, body.code.strip()):
        raise HTTPException(status_code=401, detail="Incorrect authentication code")

    token = create_access_token(
        str(user.id), extra={"role": user.role, "company_id": str(user.company_id)}
    )
    _set_auth_cookie(response, token)
    return TokenResponse(access_token=token)


@router.get("/2fa/setup", response_model=TwoFASetupResponse)
def setup_2fa(user: User = Depends(get_current_user)):
    """Generate a fresh TOTP secret and QR code. Does not save anything yet."""
    secret = generate_totp_secret()
    return TwoFASetupResponse(
        secret=secret,
        qr_data_uri=make_totp_qr_image(secret, user.email),
        otp_uri=make_totp_qr_uri(secret, user.email),
    )


@router.post("/2fa/confirm")
def confirm_2fa(
    body: TwoFAConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify the TOTP code against the provided secret, then enable 2FA."""
    if not verify_totp(body.secret, body.code.strip()):
        raise HTTPException(
            status_code=400, detail="Incorrect authentication code — try again"
        )

    user.totp_secret = body.secret
    user.totp_enabled = True
    user.totp_enrolled_at = datetime.now(timezone.utc)
    db.commit()
    log.info("2fa.enabled", user_id=str(user.id))
    return {"message": "2FA enabled"}


@router.post("/2fa/disable")
def disable_own_2fa(
    body: Disable2FARequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allow the currently logged-in user to disable their own 2FA. Requires current password."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.totp_secret = None
    user.totp_enabled = False
    user.totp_enrolled_at = None
    db.commit()
    log.info("2fa.disabled", user_id=str(user.id))
    return {"message": "2FA disabled"}


# ---------------------------------------------------------------------------
# Password management
# ---------------------------------------------------------------------------


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Authenticated password change (used for must_change_password first-login and regular changes)."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    db.commit()
    return {"message": "Password updated"}


@router.post("/reset-password/request")
def reset_password_request(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Send a password-reset link to the given email (always returns 200 to avoid enumeration)."""
    from app.core.config import settings
    from app.reports.email import send_password_reset_email

    user = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if user:
        token = generate_reset_token()
        user.password_reset_token = token
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.commit()
        reset_url = f"{settings.base_url}/set-password?token={token}"
        send_password_reset_email(
            to_email=user.email,
            to_name=user.full_name or "",
            reset_link=reset_url,
        )
        log.info("password_reset.requested", user_id=str(user.id))
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password/confirm")
def reset_password_confirm(body: ResetPasswordConfirm, db: Session = Depends(get_db)):
    """Set a new password using the token from the reset email."""
    user = db.execute(
        select(User).where(User.password_reset_token == body.token)
    ).scalar_one_or_none()

    if (
        not user
        or not user.password_reset_expires
        or user.password_reset_expires < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=400, detail="This link is invalid or has expired."
        )

    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    log.info("password_reset.confirmed", user_id=str(user.id))
    return {"message": "Password set — you can now log in."}


# ---------------------------------------------------------------------------
# Admin: reset another user's 2FA
# ---------------------------------------------------------------------------


@router.post("/2fa/reset/{user_id}")
def admin_reset_2fa(
    user_id: uuid.UUID,
    _caller: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-only: clear a user's TOTP so they can re-enrol on their new phone."""
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.totp_secret = None
    target.totp_enabled = False
    target.totp_enrolled_at = None
    db.commit()
    log.info("2fa.admin_reset", target_user_id=str(user_id), admin_id=str(_caller.id))
    return {"message": "2FA reset — user must re-enrol on next login."}
