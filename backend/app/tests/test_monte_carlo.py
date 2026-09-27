"""Test Monte Carlo Multiverse Stochastic Engine (P1 PRD §6)."""

from __future__ import annotations

import pytest

from app.engine.assumptions import load_assumptions
from app.engine.income import IncomeProfile
from app.engine.monte_carlo import run_monte_carlo
from app.engine.templates import TwinConfig
from app.schemas.input import ExistingDebt, Profile


@pytest.fixture
def assumptions():
    return load_assumptions()


@pytest.fixture
def sample_profile():
    return Profile(
        age=27,
        income_type="salary",
        income_monthly=10_000_000,
        expense_monthly=5_000_000,
        dependents_monthly=1_000_000,
        savings=25_000_000,
        existing_debt=ExistingDebt(),
    )


def test_monte_carlo_execution(assumptions, sample_profile):
    ip = IncomeProfile(income_type="salary", income_monthly=10_000_000)
    rs = assumptions.ruleset()
    cfg = TwinConfig(
        code="B",
        label="Si Penabung SBN",
        monthly_invest=2_000_000,
        instrument="bond",
    )

    res = run_monte_carlo(
        cfg=cfg,
        profile=sample_profile,
        income_profile=ip,
        assumptions=assumptions,
        ruleset=rs,
        preset_name="moderat",
        runs=100,
        horizon_months=240,
        seed=123,
    )

    assert res.twin_code == "B"
    assert res.runs == 100
    assert len(res.yearly_percentiles) == 21  # 0..20 tahun

    # Cek struktur persentil P10 <= P25 <= P50 <= P75 <= P90
    y10 = res.yearly_percentiles[10]
    nom = y10["nominal"]
    assert nom["p10"] <= nom["p25"] <= nom["p50"] <= nom["p75"] <= nom["p90"]

    real = y10["real"]
    assert real["p10"] <= real["p25"] <= real["p50"] <= real["p75"] <= real["p90"]

    # Cek metrik risiko
    assert 0.0 <= res.metrics["success_rate_positive_y10"] <= 1.0
    assert 0.0 <= res.metrics["success_rate_wealth_preservation_y10"] <= 1.0
    assert res.metrics["median_net_worth_nominal_y10"] > 0
    assert res.metrics["median_net_worth_real_y10"] > 0
