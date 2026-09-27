"""Model SQLAlchemy 2.0 untuk Financial Twin."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class AssumptionSet(Base):
    __tablename__ = "assumption_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    as_of: Mapped[datetime] = mapped_column(Date, nullable=False)
    presets: Mapped[dict] = mapped_column(JSONB, nullable=False)
    regulatory: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sources: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    input: Mapped[dict] = mapped_column(JSONB, nullable=False)
    assumption_code: Mapped[str] = mapped_column(String, nullable=False)
    assumptions_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    preset: Mapped[str] = mapped_column(String, nullable=False, default="moderat")
    engine_version: Mapped[str] = mapped_column(String, nullable=False)
    robust: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now() + interval '30 days'")
    )

    twins: Mapped[list[Twin]] = relationship(
        back_populates="simulation", cascade="all, delete-orphan", order_by="Twin.code"
    )
    recommendation: Mapped[Recommendation | None] = relationship(
        back_populates="simulation", cascade="all, delete-orphan", uselist=False
    )


class Twin(Base):
    __tablename__ = "twins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    simulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(1), nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    yearly_series: Mapped[list] = mapped_column(JSONB, nullable=False)
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    flags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    stress: Mapped[list | None] = mapped_column(JSONB)
    preset_scores: Mapped[dict | None] = mapped_column(JSONB)
    score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    narrative: Mapped[dict | None] = mapped_column(JSONB)

    simulation: Mapped[Simulation] = relationship(back_populates="twins")


class Recommendation(Base):
    __tablename__ = "recommendations"

    simulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE"), primary_key=True
    )
    best_twin: Mapped[str] = mapped_column(String(1), nullable=False)
    first_step: Mapped[str] = mapped_column(String, nullable=False)
    rationale: Mapped[str] = mapped_column(String, nullable=False)
    score_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)

    simulation: Mapped[Simulation] = relationship(back_populates="recommendation")


class ImpactEvent(Base):
    __tablename__ = "impact_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    simulation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulations.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
