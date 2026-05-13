"""Password hashing, JWT helpers, TOTP utilities, and reset-token generation."""

from __future__ import annotations

import base64
import io
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(subject: str, *, extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_minutes)).timestamp()),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_partial_token(user_id: str) -> str:
    """Short-lived JWT for the 2FA verification step (5 minutes)."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "type": "partial",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise ValueError("invalid token") from exc


def generate_reset_token() -> str:
    """Cryptographically secure URL-safe token for password reset links."""
    return secrets.token_urlsafe(32)


# ---------------------------------------------------------------------------
# TOTP helpers
# ---------------------------------------------------------------------------


def generate_totp_secret() -> str:
    import pyotp

    return pyotp.random_base32()


def make_totp_qr_uri(secret: str, email: str) -> str:
    """Return the otpauth:// URI for provisioning."""
    import pyotp

    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="Ghost CFO")


def make_totp_qr_image(secret: str, email: str) -> str:
    """Return a base64-encoded PNG data URI of the QR code."""
    import qrcode

    uri = make_totp_qr_uri(secret, email)
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def verify_totp(secret: str, code: str) -> bool:
    import pyotp

    return pyotp.TOTP(secret).verify(code, valid_window=1)
