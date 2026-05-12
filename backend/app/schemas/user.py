"""User schemas."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str | None = None  # if None, a temp password is auto-generated and emailed
    full_name: str | None = None
    role: str = "viewer"
    company_id: uuid.UUID | None = None

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        allowed = {"owner", "bookkeeper", "viewer", "admin", "tech"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    company_id: uuid.UUID | None
    active: bool
    must_change_password: bool = False
    totp_enabled: bool = False

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role: str | None = None
    company_id: uuid.UUID | None = None
    active: bool | None = None

    @field_validator("role")
    @classmethod
    def valid_role(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"owner", "bookkeeper", "viewer", "admin", "tech"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v


class UserAdminOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    company_id: uuid.UUID | None
    company_name: str | None
    active: bool
    must_change_password: bool
    totp_enabled: bool

    model_config = {"from_attributes": True}
