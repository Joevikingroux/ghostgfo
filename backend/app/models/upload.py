"""Per-month file upload bundle for Pastel Partner clients."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import Timestamps, UUIDPK


class Upload(Base, UUIDPK, Timestamps):
    __tablename__ = "uploads"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Accounting exports
    income_statement_path: Mapped[str | None] = mapped_column(Text)
    balance_sheet_path: Mapped[str | None] = mapped_column(Text)
    debtors_age_path: Mapped[str | None] = mapped_column(Text)
    creditors_age_path: Mapped[str | None] = mapped_column(Text)

    # Payroll exports
    payroll_summary_path: Mapped[str | None] = mapped_column(Text)
    payroll_employee_cost_path: Mapped[str | None] = mapped_column(Text)
    payroll_leave_path: Mapped[str | None] = mapped_column(Text)
    payroll_journal_path: Mapped[str | None] = mapped_column(Text)
    payroll_journal_integrated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

    company = relationship("Company", back_populates="uploads")
    reports = relationship("Report", back_populates="upload")
