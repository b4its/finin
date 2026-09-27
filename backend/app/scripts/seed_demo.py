"""Seed persona demo (Raka, Sinta, Dimas, Wulan) + pre-cache narasi.

Dijalankan via `make seed-demo` sebelum demo offline.
"""

from __future__ import annotations

import asyncio

from app.api.v1.simulations import _cfg_to_dict
from app.core.db import SessionLocal
from app.engine.assumptions import load_assumptions
from app.engine.runner import run_full_simulation
from app.llm.narrator import narrator
from app.models.simulation import Simulation, Twin
from app.schemas.input import (
    Decision,
    EmergencyDecision,
    ExistingDebt,
    IncomeRange,
    LoanDecision,
    Profile,
    SaveDecision,
    SimulationRequest,
    StudyDecision,
    WorkDecision,
)

PERSONAS: list[tuple[str, SimulationRequest]] = [
    (
        "Raka (20, mahasiswa)",
        SimulationRequest(
            profile=Profile(
                age=20,
                income_type="allowance",
                income_monthly=2_500_000,
                expense_monthly=2_000_000,
                savings=3_000_000,
            ),
            decisions=[
                Decision(
                    type="loan_vs_save",
                    loan=LoanDecision(kind="paylater", amount=2_000_000, tenor_months=3, rate_daily=0.002),
                    save=SaveDecision(monthly=300_000, instrument="money_market"),
                )
            ],
            preset="moderat",
        ),
    ),
    (
        "Sinta (23, fresh graduate)",
        SimulationRequest(
            profile=Profile(
                age=23,
                income_type="salary",
                income_monthly=6_000_000,
                expense_monthly=3_800_000,
                savings=10_000_000,
            ),
            decisions=[
                Decision(
                    type="study_vs_work",
                    study=StudyDecision(
                        years=2, total_cost=80_000_000, part_time_work=False, salary_premium=0.15
                    ),
                    work=WorkDecision(upskill_monthly=300_000, skill_premium=0.10, premium_after_months=12),
                )
            ],
            preset="moderat",
        ),
    ),
    (
        "Dimas (28, generasi sandwich)",
        SimulationRequest(
            profile=Profile(
                age=28,
                income_type="salary",
                income_monthly=8_000_000,
                expense_monthly=4_000_000,
                dependents_monthly=1_500_000,
                savings=4_000_000,
            ),
            decisions=[
                Decision(
                    type="emergency_vs_invest",
                    emergency=EmergencyDecision(target_months=6, invest_monthly=1_500_000),
                )
            ],
            preset="moderat",
        ),
    ),
    (
        "Wulan (26, freelancer)",
        SimulationRequest(
            profile=Profile(
                age=26,
                income_type="variable",
                income_monthly=5_500_000,
                income_range=IncomeRange(min=4_000_000, max=7_000_000),
                expense_monthly=3_200_000,
                savings=2_000_000,
                existing_debt=ExistingDebt(),
            ),
            decisions=[
                Decision(
                    type="emergency_vs_invest",
                    emergency=EmergencyDecision(target_months=4, invest_monthly=800_000),
                )
            ],
            preset="konservatif",
        ),
    ),
]


async def main() -> None:
    a = load_assumptions()
    async with SessionLocal() as session:
        for name, req in PERSONAS:
            full = run_full_simulation(req, a)
            sim = Simulation(
                input=req.model_dump(mode="json"),
                assumption_code=a.code,
                assumptions_snapshot=a.to_dict(req.preset),
                preset=req.preset,
                engine_version=a.engine_version,
                robust=full.robust,
            )
            session.add(sim)
            await session.flush()

            twin_dicts = []
            for t in full.twins:
                twin_dicts.append(
                    {
                        "code": t.cfg.code,
                        "label": t.cfg.label,
                        "description": t.cfg.description,
                        "summary": t.summary,
                        "yearly_series": t.series,
                        "flags": t.flags,
                    }
                )
            chunks = await narrator.narrate(twin_dicts)
            by_twin: dict[str, list] = {}
            for c in chunks:
                by_twin.setdefault(str(c["twin"]), []).append(c)

            for t in full.twins:
                session.add(
                    Twin(
                        simulation_id=sim.id,
                        code=t.cfg.code,
                        label=t.cfg.label,
                        config=_cfg_to_dict(t.cfg),
                        yearly_series=t.series,
                        summary=t.summary,
                        flags=t.flags,
                        stress=t.stress,
                        preset_scores=full.preset_scores.get(t.cfg.code),
                        score=round(t.score, 4),
                        narrative={"chunks": by_twin.get(str(t.cfg.code), [])},
                    )
                )
            print(f"  seeded {name}: id={sim.id} twins={[t.cfg.code for t in full.twins]}")
        await session.commit()
    print("Seed demo selesai.")


if __name__ == "__main__":
    asyncio.run(main())
