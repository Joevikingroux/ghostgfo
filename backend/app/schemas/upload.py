"""Upload and report schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class UploadOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    period_month: int
    period_year: int
    status: str
    error_message: str | None
    created_at: datetime

    income_statement_path: str | None
    balance_sheet_path: str | None
    debtors_age_path: str | None
    creditors_age_path: str | None
    payroll_summary_path: str | None
    payroll_employee_cost_path: str | None
    payroll_leave_path: str | None

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    upload_id: uuid.UUID | None
    period_month: int
    period_year: int
    metrics: dict[str, Any]
    narrative_summary: str | None
    narrative_revenue: str | None
    narrative_costs: str | None
    narrative_debtors: str | None
    narrative_payroll: str | None
    narrative_cash: str | None
    narrative_actions: str | None
    narrative_trend: str | None
    narrative_custom: str | None
    pdf_path: str | None
    email_sent: bool
    generated_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListItem(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    period_month: int
    period_year: int
    health_score: int | None = None
    health_rating: str | None = None
    pdf_ready: bool
    email_sent: bool
    payroll_pending: bool
    generated_at: datetime | None

    model_config = {"from_attributes": True}

    @classmethod
    def from_report(cls, r: Any) -> "ReportListItem":
        metrics = r.metrics or {}
        return cls(
            id=r.id,
            company_id=r.company_id,
            period_month=r.period_month,
            period_year=r.period_year,
            health_score=metrics.get("health_score"),
            health_rating=metrics.get("health_rating"),
            pdf_ready=bool(r.pdf_path),
            email_sent=r.email_sent,
            payroll_pending=bool(r.payroll_pending),
            generated_at=r.generated_at,
        )
