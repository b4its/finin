"""Benchmark engine: 4 twin × 240 bulan × 3 preset (target < 300 ms)."""

from __future__ import annotations

import statistics
import time

from app.engine.assumptions import load_assumptions
from app.engine.runner import run_full_simulation
from app.schemas.input import (
    Decision,
    LoanDecision,
    Profile,
    SaveDecision,
    SimulationRequest,
    StudyDecision,
    WorkDecision,
)

REQ = SimulationRequest(
    profile=Profile(
        age=22,
        income_type="salary",
        income_monthly=6_000_000,
        expense_monthly=3_800_000,
        dependents_monthly=500_000,
        savings=5_000_000,
    ),
    decisions=[
        Decision(
            type="loan_vs_save",
            loan=LoanDecision(kind="pinjol", amount=2_000_000, tenor_months=3, rate_daily=0.003),
            save=SaveDecision(monthly=500_000, instrument="money_market"),
        ),
        Decision(
            type="study_vs_work",
            study=StudyDecision(years=2, total_cost=80_000_000, salary_premium=0.15),
            work=WorkDecision(upskill_monthly=300_000, skill_premium=0.10, premium_after_months=12),
        ),
    ],
    preset="moderat",
)


def main() -> None:
    a = load_assumptions()
    runs = 5
    times: list[float] = []
    for _ in range(runs):
        t0 = time.perf_counter()
        full = run_full_simulation(REQ, a)
        times.append((time.perf_counter() - t0) * 1000)

    p50 = statistics.median(times)
    best = min(times)
    print(f"Engine: {len(full.twins)} twins × 240 bulan × 3 preset")
    print(f"  runs   : {runs}")
    print(f"  best   : {best:.1f} ms")
    print(f"  median : {p50:.1f} ms")
    print(f"  target : < 300 ms -> {'OK' if p50 < 300 else 'GAGAL'}")
    print("  robust :", full.robust, "| winners:", full.preset_winners)


if __name__ == "__main__":
    main()
