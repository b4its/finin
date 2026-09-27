"""Endpoint simulasi: create, get, recompute, narrative (SSE), recommendation."""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.serialization import cfg_to_dict, enriched_snapshot, preset_scores_for
from app.core.db import get_session
from app.engine.assumptions import load_assumptions
from app.engine.runner import FullSimulation, run_full_simulation
from app.llm.narrator import narrator
from app.models.simulation import Recommendation, Simulation, Twin
from app.schemas.input import RecomputeRequest, SimulationRequest
from app.schemas.output import RecommendationOut, SimulationResponse

router = APIRouter()


def _twin_to_dict(t) -> dict:  # noqa: ANN001
    return {
        "code": t.cfg.code,
        "label": t.cfg.label,
        "color": t.cfg.color,
        "dash": t.cfg.dash,
        "icon": t.cfg.icon,
        "description": t.cfg.description,
        "config": cfg_to_dict(t.cfg),
        "yearly_series": t.series,
        "summary": t.summary,
        "milestones": t.summary.get("milestones", {}),
        "flags": t.flags,
        "stress": t.stress,
        "score": round(t.score, 4),
        "score_breakdown": t.score_breakdown,
        "deleted_by_hard_rule": t.deleted_by_hard_rule,
    }


def _full_to_response(sim_id: str, full: FullSimulation, a) -> dict:  # noqa: ANN001
    return {
        "id": sim_id,
        "engine_version": a.engine_version,
        "assumption_code": a.code,
        "assumption_as_of": a.as_of,
        "preset": full.preset,
        "horizon_months": full.horizon_months,
        "twins": [_twin_to_dict(t) for t in full.twins],
        "robust": full.robust,
        "robust_reason": full.robust_reason,
        "preset_winners": full.preset_winners,
        "assumptions": enriched_snapshot(a, full),
        "market_context": a.market_context,
        "flags": full.input_flags,
        "best_twin": full.best_twin,
        "sensitivity_drivers": full.sensitivity_drivers,
    }


async def _persist(session: AsyncSession, sim: Simulation, full: FullSimulation) -> None:
    session.add(sim)
    await session.flush()
    for t in full.twins:
        ps = preset_scores_for(full, t.cfg.code)
        session.add(
            Twin(
                simulation_id=sim.id,
                code=t.cfg.code,
                label=t.cfg.label,
                config=cfg_to_dict(t.cfg),
                yearly_series=t.series,
                summary=t.summary,
                flags=t.flags,
                stress=t.stress,
                preset_scores=ps,
                score=round(t.score, 4),
            )
        )
    await session.commit()


@router.post("", response_model=SimulationResponse, status_code=201)
async def create_simulation(payload: SimulationRequest, session: AsyncSession = Depends(get_session)) -> dict:
    a = load_assumptions()
    full = run_full_simulation(payload, a)
    sim = Simulation(
        input=payload.model_dump(mode="json"),
        assumption_code=a.code,
        assumptions_snapshot=enriched_snapshot(a, full),
        preset=payload.preset,
        engine_version=a.engine_version,
        robust=full.robust,
    )
    await _persist(session, sim, full)
    return _full_to_response(str(sim.id), full, a)


async def _load_simulation(session: AsyncSession, sim_id: str) -> Simulation:
    try:
        uid = uuid.UUID(sim_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "ID tidak valid"}) from e
    sim = await session.get(Simulation, uid)
    if sim is None:
        raise HTTPException(
            status_code=404, detail={"code": "NOT_FOUND", "message": "Simulasi tidak ditemukan"}
        )
    return sim


def _stored_to_response(sim: Simulation, twins: list[Twin]) -> dict:
    a = load_assumptions(sim.assumption_code)
    snapshot = sim.assumptions_snapshot
    meta = snapshot.get("_meta", {}) if isinstance(snapshot, dict) else {}
    return {
        "id": str(sim.id),
        "engine_version": sim.engine_version,
        "assumption_code": sim.assumption_code,
        "assumption_as_of": a.as_of,
        "preset": sim.preset,
        "horizon_months": meta.get("horizon_months", 240),
        "twins": [
            {
                "code": t.code,
                "label": t.label,
                "color": t.config.get("_color", "#94A3B8"),
                "dash": t.config.get("_dash", "solid"),
                "icon": t.config.get("_icon", "circle"),
                "description": t.config.get("description", ""),
                "config": t.config,
                "yearly_series": t.yearly_series,
                "summary": t.summary,
                "milestones": (t.summary or {}).get("milestones", {}),
                "flags": t.flags,
                "stress": t.stress or [],
                "score": float(t.score) if t.score is not None else 0.0,
                "score_breakdown": (t.preset_scores or {}).get("_breakdown", {}),
                "deleted_by_hard_rule": bool((t.preset_scores or {}).get("_deleted_by_hard_rule", False)),
            }
            for t in twins
        ],
        "robust": bool(sim.robust),
        "robust_reason": meta.get("robust_reason", ""),
        "preset_winners": meta.get("preset_winners", {}),
        "assumptions": snapshot,
        "market_context": a.market_context,
        "flags": meta.get("input_flags", []),
        "best_twin": meta.get("best_twin", "0"),
        "sensitivity_drivers": meta.get("sensitivity_drivers", []),
    }


@router.get("/{sim_id}", response_model=SimulationResponse)
async def get_simulation(sim_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    sim = await _load_simulation(session, sim_id)
    result = await session.execute(select(Twin).where(Twin.simulation_id == sim.id).order_by(Twin.code))
    twins = list(result.scalars().all())
    return _stored_to_response(sim, twins)


@router.post("/{sim_id}/recompute", response_model=SimulationResponse)
async def recompute(
    sim_id: str, payload: RecomputeRequest, session: AsyncSession = Depends(get_session)
) -> dict:
    sim = await _load_simulation(session, sim_id)
    base_req = SimulationRequest.model_validate(sim.input)
    new_req = base_req.model_copy(
        update={
            "preset": payload.preset or base_req.preset,
            "assumption_overrides": {**base_req.assumption_overrides, **payload.assumption_overrides},
        }
    )
    a = load_assumptions()
    full = run_full_simulation(new_req, a)

    # ganti twin lama
    result = await session.execute(select(Twin).where(Twin.simulation_id == sim.id))
    for old in result.scalars().all():
        await session.delete(old)
    sim.preset = new_req.preset
    sim.assumptions_snapshot = enriched_snapshot(a, full)
    sim.robust = full.robust
    await session.flush()
    for tr in full.twins:
        ps = preset_scores_for(full, tr.cfg.code)
        session.add(
            Twin(
                simulation_id=sim.id,
                code=tr.cfg.code,
                label=tr.cfg.label,
                config=cfg_to_dict(tr.cfg),
                yearly_series=tr.series,
                summary=tr.summary,
                flags=tr.flags,
                stress=tr.stress,
                preset_scores=ps,
                score=round(tr.score, 4),
            )
        )
    await session.commit()
    return _full_to_response(str(sim.id), full, a)


@router.get("/{sim_id}/narrative")
async def narrative(sim_id: str, session: AsyncSession = Depends(get_session)) -> StreamingResponse:
    sim = await _load_simulation(session, sim_id)
    result = await session.execute(select(Twin).where(Twin.simulation_id == sim.id).order_by(Twin.code))
    twins = list(result.scalars().all())

    twin_dicts = [
        {
            "code": t.code,
            "label": t.label,
            "description": t.config.get("description", ""),
            "summary": t.summary,
            "yearly_series": t.yearly_series,
            "flags": t.flags,
        }
        for t in twins
    ]

    async def gen():
        chunks = await narrator.narrate(twin_dicts)
        # cache ke DB
        by_twin: dict[str, list] = {}
        for c in chunks:
            by_twin.setdefault(str(c["twin"]), []).append(c)
        for t in twins:
            if str(t.code) in by_twin:
                t.narrative = {"chunks": by_twin[str(t.code)]}
        await session.commit()
        for c in chunks:
            yield f"data: {json.dumps(c, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{sim_id}/recommendation", response_model=RecommendationOut)
async def recommendation(sim_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    sim = await _load_simulation(session, sim_id)
    result = await session.execute(select(Twin).where(Twin.simulation_id == sim.id).order_by(Twin.code))
    twins = list(result.scalars().all())
    twin_dicts = [
        {
            "code": t.code,
            "label": t.label,
            "description": t.config.get("description", ""),
            "summary": t.summary,
            "yearly_series": t.yearly_series,
            "flags": t.flags,
            "meta": t.config.get("meta", {}),
            "score": float(t.score) if t.score is not None else 0.0,
            "score_breakdown": (t.preset_scores or {}).get("_breakdown", {}),
        }
        for t in twins
    ]
    meta = (sim.assumptions_snapshot or {}).get("_meta", {})
    # Gunakan twin terbaik yang sama dengan scoring engine (bukan definisi lain).
    best_code = meta.get("best_twin")
    candidates = [t for t in twin_dicts if t["code"] != "0"] or twin_dicts
    best = next((t for t in candidates if t["code"] == best_code), None)
    if best is None:
        best = max(candidates, key=lambda t: t.get("score", 0.0))
    others = [t for t in candidates if t["code"] != best["code"]]

    rec = await narrator.recommend(best, others, bool(sim.robust))
    breakdown = best.get("score_breakdown", {})

    stored = await session.get(Recommendation, sim.id)
    if stored is None:
        stored = Recommendation(
            simulation_id=sim.id,
            best_twin=best["code"],
            first_step=rec["first_step"],
            rationale=rec["rationale"],
            score_breakdown=breakdown,
            source=rec["source"],
        )
        session.add(stored)
    else:
        stored.best_twin = best["code"]
        stored.first_step = rec["first_step"]
        stored.rationale = rec["rationale"]
        stored.score_breakdown = breakdown
        stored.source = rec["source"]
    await session.commit()

    return {
        "simulation_id": str(sim.id),
        "best_twin": best["code"],
        "best_label": best["label"],
        "first_step": rec["first_step"],
        "rationale": rec["rationale"],
        "score_breakdown": breakdown,
        "source": rec["source"],
    }


@router.get("/{sim_id}/export/csv")
async def export_simulation_csv(sim_id: str, session: AsyncSession = Depends(get_session)) -> Response:
    """Ekspor trajektori bulanan lengkap (240 bulan) seluruh kembar dalam format CSV."""
    sim = await _load_simulation(session, sim_id)
    req = SimulationRequest.model_validate(sim.input)
    a = load_assumptions(sim.assumption_code)
    full = run_full_simulation(req, a)

    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM untuk Excel
    writer = csv.writer(output)
    writer.writerow(
        [
            "Twin Code",
            "Twin Label",
            "Month",
            "Year",
            "Income Nominal",
            "Living Cost",
            "Debt Payment",
            "Cash Balance",
            "Investment Balance",
            "Debt Balance",
            "Net Worth Nominal",
            "Net Worth Real",
            "Emergency Fund Months",
            "DSR Ratio",
            "Defaulted",
        ]
    )

    for tr in full.twins:
        for m in tr.result.months:
            writer.writerow(
                [
                    tr.cfg.code,
                    tr.cfg.label,
                    m.month,
                    m.month // 12,
                    round(m.income, 2),
                    round(m.living, 2),
                    round(m.paid_debt, 2),
                    round(m.cash, 2),
                    round(m.invest, 2),
                    round(m.debt, 2),
                    round(m.net_worth, 2),
                    round(m.net_worth_real, 2),
                    round(m.emergency_months, 2),
                    round(m.dsr, 4),
                    m.defaulted,
                ]
            )

    filename = f"financial-twin-{sim_id[:8]}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{sim_id}/export/json")
async def export_simulation_json(sim_id: str, session: AsyncSession = Depends(get_session)) -> Response:
    """Ekspor paket data simulasi lengkap & audit trail dalam format JSON."""
    sim = await _load_simulation(session, sim_id)
    result = await session.execute(select(Twin).where(Twin.simulation_id == sim.id).order_by(Twin.code))
    twins = list(result.scalars().all())
    data = _stored_to_response(sim, twins)
    data["input"] = sim.input
    data["exported_at"] = datetime.now(UTC).isoformat()

    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    filename = f"financial-twin-{sim_id[:8]}.json"
    return Response(
        content=json_str,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{sim_id}/monte-carlo")
async def get_simulation_monte_carlo(
    sim_id: str,
    twin_code: str = "0",
    runs: int = 500,
    preset: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Simulasi stokastik Monte Carlo (P1 PRD §6) untuk mengevaluasi pita probabilitas (P10-P90)."""
    from app.engine.monte_carlo import run_monte_carlo
    from app.engine.runner import income_profile_from

    sim = await _load_simulation(session, sim_id)
    req = SimulationRequest.model_validate(sim.input)
    a = load_assumptions(sim.assumption_code)
    full = run_full_simulation(req, a)

    target_twin = next((t for t in full.twins if t.cfg.code == twin_code), None)
    if target_twin is None:
        raise HTTPException(status_code=404, detail=f"Twin dengan kode '{twin_code}' tidak ditemukan")

    clamped_runs = max(50, min(runs, 1000))
    preset_name = preset or full.preset
    inc_profile = income_profile_from(req.profile)

    mc_result = run_monte_carlo(
        cfg=target_twin.cfg,
        profile=req.profile,
        income_profile=inc_profile,
        assumptions=a,
        ruleset=a.ruleset(),
        preset_name=preset_name,
        runs=clamped_runs,
        horizon_months=req.horizon_months,
    )
    return mc_result.to_dict()
