"""Generated monthly report ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import Timestamps, UUIDPK


class Report(Base, UUIDPK, Timestamps):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "period_month", "period_year", name="uq_report_period"
        ),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    upload_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploads.id"), nullable=True
    )

    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)

    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    narrative_summary: Mapped[str | None] = mapped_column(Text)
    narrative_revenue: Mapped[str | None] = mapped_column(Text)
    narrative_costs: Mapped[str | None] = mapped_column(Text)
    narrative_debtors: Mapped[str | None] = mapped_column(Text)
    narrative_payroll: Mapped[str | None] = mapped_column(Text)
    narrative_cash: Mapped[str | None] = mapped_column(Text)
    narrative_actions: Mapped[str | None] = mapped_column(Text)
    narrative_trend: Mapped[str | None] = mapped_column(
        Text
    )  # Premium: YoY + quarterly
    narrative_custom: Mapped[str | None] = mapped_column(
        Text
    )  # Premium: admin commentary

    pdf_path: Mapped[str | None] = mapped_column(Text)

    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    telegram_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    telegram_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payroll_pending: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    company = relationship("Company", back_populates="reports")
    upload = relationship("Upload", back_populates="reports")
