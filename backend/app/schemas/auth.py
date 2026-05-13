"""Auth request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    requires_2fa: bool = False
    partial_token: str | None = None


class TwoFAVerifyRequest(BaseModel):
    partial_token: str
    code: str


class TwoFAConfirmRequest(BaseModel):
    secret: str
    code: str


class TwoFASetupResponse(BaseModel):
    secret: str
    qr_data_uri: str
    otp_uri: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class Disable2FARequest(BaseModel):
    current_password: str


class UserMe(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    company_id: str | None
    must_change_password: bool = False
    totp_enabled: bool = False

    model_config = {"from_attributes": True}
