"""Simulasi Monte Carlo Multiverse (P1 PRD §6).

Menghasilkan pita probabilitas trajektori kekayaan (P10, P25, P50, P75, P90)
berdasarkan distribusi volatilitas stokastik instrumen keuangan dan inflasi Indonesia.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from app.engine.assumptions import Assumptions
from app.engine.income import IncomeProfile, income_path
from app.engine.loans import LoanState, apply_month
from app.engine.templates import TwinConfig
from app.schemas.input import Profile

# Volatilitas tahunan (standar deviasi sigma) acuan pasar modal & makro RI (2026)
VOLATILITY_MAP: dict[str, float] = {
    "stock": 0.16,  # IHSG / Indeks Saham (~16%/tahun)
    "bond": 0.04,  # SBN Ritel / Sukuk Negara (~4%/tahun)
    "money_market": 0.012,  # Reksadana Pasar Uang (~1,2%/tahun)
    "savings": 0.005,  # Tabungan Bank Reguler
    "deposit": 0.008,  # Deposito Berjangka
    "inflation": 0.015,  # Volatilitas inflasi IHK (~1,5%/tahun)
}


@dataclass
class MonteCarloResult:
    twin_code: str
    twin_label: str
    runs: int
    yearly_percentiles: list[dict[str, Any]]
    metrics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "twin_code": self.twin_code,
            "twin_label": self.twin_label,
            "runs": self.runs,
            "yearly_percentiles": self.yearly_percentiles,
            "metrics": self.metrics,
        }


def _percentile(sorted_vals: list[float], pct: float) -> float:
    """Ambil nilai persentil dari daftar float terurut."""
    if not sorted_vals:
        return 0.0
    idx = int(pct * (len(sorted_vals) - 1))
    return sorted_vals[idx]


def run_monte_carlo(
    cfg: TwinConfig,
    profile: Profile,
    income_profile: IncomeProfile,
    assumptions: Assumptions,
    ruleset: dict,
    *,
    preset_name: str = "moderat",
    runs: int = 500,
    horizon_months: int = 240,
    seed: int | None = 42,
) -> MonteCarloResult:
    """Jalankan N simulasi stokastik Monte Carlo untuk satu twin."""
    rng = random.Random(seed) if seed is not None else random.Random()

    preset = assumptions.preset(preset_name)
    base_infl = float(preset.get("inflation", 0.03))
    base_inv = float(preset.get(cfg.instrument, 0.045))
    base_cash = float(preset.get("savings", 0.01))
    growth = float(preset.get("salary_growth", 0.05))
    job_wait = int(preset.get("job_wait_months", 3))

    sigma_inv = VOLATILITY_MAP.get(cfg.instrument, 0.04)
    sigma_infl = VOLATILITY_MAP.get("inflation", 0.015)

    base_expense = profile.expense_monthly + profile.dependents_monthly
    emergency_target = base_expense * cfg.emergency_target_months

    # Simpan hasil tiap run: run_idx -> year (0..20) -> (nominal_nw, real_nw)
    num_years = horizon_months // 12
    trajectories_nominal: list[list[float]] = [[] for _ in range(num_years + 1)]
    trajectories_real: list[list[float]] = [[] for _ in range(num_years + 1)]

    y10_real_list: list[float] = []
    y10_nominal_list: list[float] = []

    for _ in range(runs):
        cash = profile.savings
        invest = 0.0

        if cfg.initial_dp > 0:
            cash = max(0.0, cash - cfg.initial_dp)

        from app.engine.loans import Loan

        # Inisialisasi pinjaman independen untuk tiap run
        loans: list[LoanState] = []
        if profile.existing_debt.principal > 0:
            debt_loan = Loan(
                kind="annuity",
                principal=profile.existing_debt.principal,
                tenor_months=profile.existing_debt.tenor_months or 12,
                annual_rate=profile.existing_debt.annual_rate or 0.0,
                ruleset=ruleset,
            )
            loans.append(LoanState(debt_loan))
        if cfg.loan is not None:
            loans.append(LoanState(cfg.loan))

        cum_infl = 1.0

        # Catat th 0
        debt_init = sum(ls.balance for ls in loans if not ls.closed)
        nw_init = cash + invest + cfg.property_initial_value + cfg.vehicle_initial_value - debt_init
        trajectories_nominal[0].append(nw_init)
        trajectories_real[0].append(nw_init)

        for m in range(1, horizon_months + 1):
            # Syok stokastik bulanan
            z_infl = rng.gauss(0.0, 1.0)
            z_inv = rng.gauss(0.0, 1.0)

            # Laju inflasi bulanan acak
            m_infl = max(0.0005, (base_infl / 12.0) + (sigma_infl / math.sqrt(12.0)) * z_infl)
            cum_infl *= 1.0 + m_infl

            # Laju imbal hasil investasi bulanan acak
            m_inv = max(-0.15, (base_inv / 12.0) + (sigma_inv / math.sqrt(12.0)) * z_inv)
            m_cash = max(0.0, base_cash / 12.0)

            # Pendapatan deterministik jalur karier + laba bisnis
            income = (
                income_path(
                    income_profile,
                    growth,
                    m,
                    study=cfg.study,
                    part_time_monthly=cfg.part_time_monthly,
                    job_wait_months=job_wait,
                    graduate_month=cfg.graduate_month,
                    post_graduate_multiplier=cfg.post_graduate_multiplier,
                    skill_month=cfg.skill_month,
                    skill_multiplier=cfg.skill_multiplier,
                )
                + cfg.business_profit_monthly
            )

            rent_cost = cfg.rent_monthly * cum_infl if cfg.rent_monthly > 0 else 0.0
            extra_cost = cfg.study_cost + cfg.upskill_monthly + rent_cost + cfg.insurance_monthly
            living = (
                (profile.expense_monthly * cum_infl) + (profile.dependents_monthly * cum_infl) + extra_cost
            )

            available = income - living

            paid_total = 0.0
            cash_used_total = 0.0
            for ls in loans:
                paid, cash_used, _ = apply_month(ls, available - paid_total, cash)
                paid_total += paid
                cash_used_total += cash_used
            cash -= cash_used_total

            surplus = available - paid_total

            if surplus >= 0:
                if cfg.emergency_first and cash < emergency_target:
                    room = emergency_target - cash
                    to_emergency = min(surplus, room)
                    cash += to_emergency
                    surplus -= to_emergency

                contrib = min(surplus, cfg.monthly_invest)
                invest += contrib
                cash += surplus - contrib
            else:
                cash += surplus
                if cash < 0:
                    invest += cash
                    cash = 0.0
                    if invest < 0:
                        invest = 0.0

            invest *= 1.0 + m_inv
            cash *= 1.0 + m_cash

            # Evaluasi di titik tahunan (m % 12 == 0)
            if m % 12 == 0:
                yr = m // 12
                prop_val = (
                    cfg.property_initial_value * (1.0 + cfg.property_appreciation_annual / 12.0) ** m
                    if cfg.property_initial_value > 0
                    else 0.0
                )
                veh_val = (
                    cfg.vehicle_initial_value * max(0.05, (1.0 - cfg.vehicle_depreciation_annual / 12.0) ** m)
                    if cfg.vehicle_initial_value > 0
                    else 0.0
                )
                debt_bal = sum(ls.balance for ls in loans if not ls.closed)
                tot_invest = max(invest, 0.0) + prop_val + veh_val
                nw_nom = cash + tot_invest - debt_bal
                nw_real = nw_nom / cum_infl

                trajectories_nominal[yr].append(nw_nom)
                trajectories_real[yr].append(nw_real)

                if yr == 10:
                    y10_real_list.append(nw_real)
                    y10_nominal_list.append(nw_nom)

    # Susun persentil tahunan 0..20
    yearly_percentiles: list[dict[str, Any]] = []
    for y in range(num_years + 1):
        s_nom = sorted(trajectories_nominal[y])
        s_real = sorted(trajectories_real[y])

        yearly_percentiles.append(
            {
                "year": y,
                "nominal": {
                    "p10": round(_percentile(s_nom, 0.10)),
                    "p25": round(_percentile(s_nom, 0.25)),
                    "p50": round(_percentile(s_nom, 0.50)),
                    "p75": round(_percentile(s_nom, 0.75)),
                    "p90": round(_percentile(s_nom, 0.90)),
                },
                "real": {
                    "p10": round(_percentile(s_real, 0.10)),
                    "p25": round(_percentile(s_real, 0.25)),
                    "p50": round(_percentile(s_real, 0.50)),
                    "p75": round(_percentile(s_real, 0.75)),
                    "p90": round(_percentile(s_real, 0.90)),
                },
            }
        )

    # Analisis metrik risiko & keandalan di Tahun ke-10
    sorted_y10_nom = sorted(y10_nominal_list) if y10_nominal_list else [0.0]
    sorted_y10_real = sorted(y10_real_list) if y10_real_list else [0.0]

    positive_count = sum(1 for v in sorted_y10_real if v > 0)
    success_rate_positive = positive_count / len(sorted_y10_real) if sorted_y10_real else 0.0

    wealth_preservation_count = sum(1 for v in sorted_y10_real if v >= profile.savings)
    success_rate_preservation = wealth_preservation_count / len(sorted_y10_real) if sorted_y10_real else 0.0

    # Value at Risk 95% (persentil 5)
    var_95 = _percentile(sorted_y10_nom, 0.05)
    cvar_cutoff = max(1, int(0.05 * len(sorted_y10_nom)))
    cvar_95 = sum(sorted_y10_nom[:cvar_cutoff]) / cvar_cutoff

    metrics = {
        "success_rate_positive_y10": round(success_rate_positive, 4),
        "success_rate_wealth_preservation_y10": round(success_rate_preservation, 4),
        "median_net_worth_nominal_y10": round(_percentile(sorted_y10_nom, 0.50)),
        "median_net_worth_real_y10": round(_percentile(sorted_y10_real, 0.50)),
        "p10_net_worth_y10": round(_percentile(sorted_y10_nom, 0.10)),
        "p90_net_worth_y10": round(_percentile(sorted_y10_nom, 0.90)),
        "var_95_nominal_y10": round(var_95),
        "cvar_95_nominal_y10": round(cvar_95),
        "preset_used": preset_name,
        "instrument_volatility": sigma_inv,
        "inflation_volatility": sigma_infl,
    }

    return MonteCarloResult(
        twin_code=cfg.code,
        twin_label=cfg.label,
        runs=runs,
        yearly_percentiles=yearly_percentiles,
        metrics=metrics,
    )
