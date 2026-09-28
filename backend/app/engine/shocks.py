"""Stress test "Bagaimana jika?" — 2 guncangan satu klik.

(a) kehilangan penghasilan 3 bulan
(b) biaya darurat sebesar 2x pengeluaran bulanan di tahun ke-2

Twin dinyatakan bertahan jika kas + investasi tidak habis (tidak perlu
berutang baru) selama guncangan.
"""

from __future__ import annotations

from app.engine.assumptions import Assumptions
from app.engine.income import IncomeProfile
from app.engine.simulator import Shock, simulate
from app.engine.templates import TwinConfig
from app.schemas.input import Profile


def default_shocks(profile: Profile) -> list[Shock]:
    monthly_expense = profile.expense_monthly + profile.dependents_monthly
    return [
        Shock(
            code="income_loss_3m",
            label="Kehilangan penghasilan 3 bulan",
            start_month=6,
            income_multiplier=0.0,
            duration_months=3,
            note="Pendapatan berhenti total selama 3 bulan pada bulan ke-7.",
        ),
        Shock(
            code="emergency_cost_2x",
            label="Biaya darurat 2× pengeluaran di tahun ke-2",
            start_month=24,
            income_multiplier=1.0,
            duration_months=1,
            extra_cost=monthly_expense * 2.0,
            note="Biaya tak terduga sebesar 2× pengeluaran bulanan pada tahun ke-2.",
        ),
    ]


def run_stress(
    cfg: TwinConfig,
    profile: Profile,
    income_profile: IncomeProfile,
    assumptions: Assumptions,
    ruleset: dict,
    *,
    months: int = 240,
) -> list[dict]:
    preset = assumptions.preset("moderat")
    out: list[dict] = []
    for shock in default_shocks(profile):
        res = simulate(
            cfg,
            profile,
            income_profile,
            preset,
            ruleset,
            months=months,
            shock=shock,
            use_min_income=True,
        )
        # Twin bertahan jika kas tidak pernah menyentuh 0 (masih punya bantalan
        # likuid) DAN tidak terpaksa menambah utang baru kapan pun selama horizon.
        min_cash = min(m.cash for m in res.months)
        new_debt = max(m.new_debt for m in res.months)
        worst_month = min(range(len(res.months)), key=lambda i: res.months[i].net_worth)
        survived = min_cash > 0 and new_debt == 0
        out.append(
            {
                "shock": shock.code,
                "label": shock.label,
                "survived": bool(survived),
                "min_cash": min_cash,
                "new_debt": new_debt,
                "worst_month": worst_month,
                "note": shock.note,
            }
        )
    return out
