"""Company (SMB client) ORM model."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models._mixins import Timestamps, UUIDPK


class Company(Base, UUIDPK, Timestamps):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trading_name: Mapped[str | None] = mapped_column(String(255))
    reg_number: Mapped[str | None] = mapped_column(String(64))
    vat_number: Mapped[str | None] = mapped_column(String(64))
    industry: Mapped[str | None] = mapped_column(String(128))

    owner_name: Mapped[str | None] = mapped_column(String(255))
    owner_email: Mapped[str | None] = mapped_column(String(255))
    owner_telegram: Mapped[str | None] = mapped_column(String(32))
    bookkeeper_name: Mapped[str | None] = mapped_column(String(255))
    bookkeeper_email: Mapped[str | None] = mapped_column(String(255))

    plan: Mapped[str] = mapped_column(String(32), default="starter", nullable=False)
    plan_start_date: Mapped[date | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # PayFast subscription
    payfast_token: Mapped[str | None] = mapped_column(Text)
    subscription_status: Mapped[str] = mapped_column(
        String(32), default="inactive", nullable=False
    )

    data_source: Mapped[str] = mapped_column(
        String(32), default="partner", nullable=False
    )
    language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)

    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    uploads = relationship(
        "Upload", back_populates="company", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="company", cascade="all, delete-orphan"
    )
    evolution_agent = relationship(
        "EvolutionAgent",
        back_populates="company",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Company {self.name}>"
