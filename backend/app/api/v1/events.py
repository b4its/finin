"""Endpoint event dampak (anonim): fsc_pre, fsc_post, commit."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.simulation import ImpactEvent, Simulation
from app.schemas.input import EventRequest

router = APIRouter()


@router.post("/simulations/{sim_id}/events", status_code=201)
async def record_event(
    sim_id: str, payload: EventRequest, session: AsyncSession = Depends(get_session)
) -> dict:
    try:
        uid = uuid.UUID(sim_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"}) from e
    sim = await session.get(Simulation, uid)
    if sim is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND"})
    ev = ImpactEvent(simulation_id=uid, kind=payload.kind, value=payload.value)
    session.add(ev)
    await session.commit()
    return {"id": ev.id, "kind": ev.kind, "value": ev.value}


@router.get("/impact/summary")
async def impact_summary(session: AsyncSession = Depends(get_session)) -> dict:
    async def avg(kind: str) -> float | None:
        r = await session.execute(
            select(func.avg(ImpactEvent.value)).where(
                ImpactEvent.kind == kind, ImpactEvent.value.is_not(None)
            )
        )
        v = r.scalar()
        return float(v) if v is not None else None

    pre = await avg("fsc_pre")
    post = await avg("fsc_post")
    commits = await session.execute(select(func.count()).where(ImpactEvent.kind == "commit"))
    total_sims = await session.execute(select(func.count()).select_from(Simulation))
    n_commit = commits.scalar() or 0
    n_sims = total_sims.scalar() or 0
    return {
        "fsc_pre_avg": pre,
        "fsc_post_avg": post,
        "fsc_delta": (post - pre) if (pre is not None and post is not None) else None,
        "commits": n_commit,
        "simulations": n_sims,
        "commit_rate": (n_commit / n_sims) if n_sims else None,
    }
