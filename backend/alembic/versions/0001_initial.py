"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "assumption_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("presets", postgresql.JSONB(), nullable=False),
        sa.Column("regulatory", postgresql.JSONB(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "simulations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("input", postgresql.JSONB(), nullable=False),
        sa.Column("assumption_code", sa.String(), nullable=False),
        sa.Column("assumptions_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("preset", sa.String(), nullable=False, server_default="moderat"),
        sa.Column("engine_version", sa.String(), nullable=False),
        sa.Column("robust", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), server_default=sa.text("now() + interval '30 days'")),
    )

    op.create_table(
        "twins",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column(
            "simulation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("simulations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(1), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("yearly_series", postgresql.JSONB(), nullable=False),
        sa.Column("summary", postgresql.JSONB(), nullable=False),
        sa.Column("flags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("stress", postgresql.JSONB(), nullable=True),
        sa.Column("preset_scores", postgresql.JSONB(), nullable=True),
        sa.Column("score", sa.Numeric(5, 4), nullable=True),
        sa.Column("narrative", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("simulation_id", "code", name="uq_twin_sim_code"),
    )

    op.create_table(
        "recommendations",
        sa.Column(
            "simulation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("simulations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("best_twin", sa.String(1), nullable=False),
        sa.Column("first_step", sa.String(), nullable=False),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("score_breakdown", postgresql.JSONB(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
    )

    op.create_table(
        "impact_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "simulation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("simulations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("value", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("impact_events")
    op.drop_table("recommendations")
    op.drop_table("twins")
    op.drop_table("simulations")
    op.drop_table("assumption_sets")
