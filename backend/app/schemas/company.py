"""Company schemas."""
from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, EmailStr


class CompanyCreate(BaseModel):
    name: str
    trading_name: str | None = None
    reg_number: str | None = None
    vat_number: str | None = None
    industry: str | None = None
    owner_name: str | None = None
    owner_email: EmailStr | None = None
    owner_whatsapp: str | None = None
    bookkeeper_name: str | None = None
    bookkeeper_email: EmailStr | None = None
    plan: str = "starter"
    data_source: str = "partner"
    language: str = "en"


class CompanyUpdate(BaseModel):
    name: str | None = None
    trading_name: str | None = None
    owner_name: str | None = None
    owner_email: EmailStr | None = None
    owner_whatsapp: str | None = None
    bookkeeper_name: str | None = None
    bookkeeper_email: EmailStr | None = None
    language: str | None = None
    # Admin-only fields (stripped for non-admin callers in the endpoint)
    plan: str | None = None
    active: bool | None = None
    data_source: str | None = None


class CompanyOut(BaseModel):
    id: uuid.UUID
    name: str
    trading_name: str | None
    industry: str | None
    owner_name: str | None
    owner_email: str | None
    owner_whatsapp: str | None
    bookkeeper_name: str | None
    bookkeeper_email: str | None
    plan: str
    active: bool
    data_source: str
    language: str
    plan_start_date: date | None

    model_config = {"from_attributes": True}
