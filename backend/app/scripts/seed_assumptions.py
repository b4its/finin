"""Seed set asumsi default dari data/assumptions/<CODE>.json ke DB."""

from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.engine.assumptions import load_assumptions
from app.models.simulation import AssumptionSet


async def main() -> None:
    a = load_assumptions()
    async with SessionLocal() as session:
        existing = await session.execute(select(AssumptionSet).where(AssumptionSet.code == a.code))
        row = existing.scalar_one_or_none()
        if row is None:
            row = AssumptionSet(
                code=a.code,
                as_of=date.fromisoformat(a.as_of),
                presets=a.presets,
                regulatory=a.regulatory,
                sources=a.sources,
                is_default=True,
            )
            session.add(row)
        else:
            row.presets = a.presets
            row.regulatory = a.regulatory
            row.sources = a.sources
            row.is_default = True
        # pastikan hanya satu default
        others = await session.execute(select(AssumptionSet).where(AssumptionSet.code != a.code))
        for o in others.scalars().all():
            o.is_default = False
        await session.commit()
    print(f"Seeded assumption set: {settings.assumption_set} ({a.as_of})")


if __name__ == "__main__":
    asyncio.run(main())
