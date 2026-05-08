"""Auth request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserMe(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    company_id: str | None

    model_config = {"from_attributes": True}
