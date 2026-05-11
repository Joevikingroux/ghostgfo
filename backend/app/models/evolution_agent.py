"""Per-company Pastel Evolution agent configuration."""
from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import UUIDPK


class EvolutionAgent(Base, UUIDPK):
    __tablename__ = "evolution_agents"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    api_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    server_name: Mapped[str | None] = mapped_column(String(255))
    db_name: Mapped[str | None] = mapped_column(String(255))
    db_username: Mapped[str | None] = mapped_column(String(255))
    db_password: Mapped[str | None] = mapped_column(String(255))
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_status: Mapped[str | None] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Set when a bookkeeper submits payroll files and wants a report generated.
    # Agent polls /status, sees these, runs a sync for that period, then clears them.
    pending_sync_month: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    pending_sync_year: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    company = relationship("Company", back_populates="evolution_agent")
