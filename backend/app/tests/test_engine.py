"""Test engine: loans, income, simulator, shocks, sensitivity, scoring."""

from __future__ import annotations

import pytest

from app.engine.assumptions import load_assumptions, monthly_rate
from app.engine.income import IncomeProfile
from app.engine.loans import Loan, LoanState, annuity_payment, apply_month, flat_monthly_payment
from app.engine.runner import run_full_simulation
from app.engine.simulator import Shock, simulate
from app.engine.templates import build_twins, twins_for_decision
from app.schemas.input import (
    Decision,
    EmergencyDecision,
    ExistingDebt,
    LoanDecision,
    Profile,
    SaveDecision,
    SimulationRequest,
    StudyDecision,
    WorkDecision,
)


@pytest.fixture
def assumptions():
    return load_assumptions()


@pytest.fixture
def profile():
    return Profile(
        age=23,
        income_type="salary",
        income_monthly=6_000_000,
        expense_monthly=3_800_000,
        dependents_monthly=500_000,
        savings=10_000_000,
        existing_debt=ExistingDebt(),
    )


def test_annuity_vs_manual():
    # 12 juta, 12% tahunan, 12 bulan
    p = annuity_payment(12_000_000, 0.12, 12)
    # rumus manual: i=0.01, P = 12jt*0.01/(1-1.01^-12)
    manual = 12_000_000 * 0.01 / (1 - 1.01**-12)
    assert abs(p - manual) < 1.0


def test_annuity_zero_rate():
    assert annuity_payment(1_200_000, 0.0, 12) == 100_000


def test_flat_payment_with_lock_cap():
    # bunga ekstrem -> cicilan = (pokok + pokok)/tenor
    p = flat_monthly_payment(1_000_000, 0.5, 6)
    assert abs(p - (2_000_000 / 6)) < 1.0


def test_annuity_charges_real_interest():
    """Anuitas harus mengenakan bunga nyata: total terbayar > pokok."""
    loan = Loan(kind="annuity", principal=120_000_000, tenor_months=60, annual_rate=0.12)
    st = LoanState(loan=loan)
    total_paid = 0.0
    for _ in range(60):
        paid, _, _ = apply_month(st, income_available=10_000_000, cash_available=0)
        total_paid += paid
    # 12%/th, 5 tahun -> bunga ~30%; total harus jelas > pokok
    assert total_paid > 120_000_000 * 1.2
    assert st.closed
    assert abs(st.balance) < 1.0


def test_flat_loan_total_equals_principal_plus_fee():
    """Flat: total terbayar = pokok + manfaat (lock cap)."""
    from app.engine.regulatory import total_fee

    loan = Loan(kind="pinjol", principal=2_000_000, tenor_months=3, rate_daily=0.003)
    st = LoanState(loan=loan)
    total_paid = 0.0
    for _ in range(3):
        paid, _, _ = apply_month(st, income_available=5_000_000, cash_available=0)
        total_paid += paid
    expected = 2_000_000 + total_fee(2_000_000, 0.003, 3)
    assert abs(total_paid - expected) < 1.0
    assert st.closed


def test_annuity_payment_formula_manual():
    p = annuity_payment(50_000_000, 0.10, 36)
    i = 0.10 / 12
    manual = 50_000_000 * i / (1 - (1 + i) ** -36)
    assert abs(p - manual) < 1e-6


def test_monthly_rate_conversion():
    assert abs(monthly_rate(0.12) - (1.12 ** (1 / 12) - 1)) < 1e-12


def test_inflation_zero_real_equals_nominal(assumptions):
    a = load_assumptions()
    preset = a.preset("moderat")
    preset["inflation"] = 0.0
    cfg = build_twins(
        Profile(age=23, income_monthly=6_000_000, expense_monthly=3_000_000, savings=5_000_000),
        IncomeProfile("salary", 6_000_000),
        [],
        a.ruleset(),
        0.05,
        a.common,
    )[0]
    res = simulate(
        cfg,
        Profile(age=23, income_monthly=6_000_000, expense_monthly=3_000_000, savings=5_000_000),
        IncomeProfile("salary", 6_000_000),
        preset,
        a.ruleset(),
        months=120,
    )
    s = res.at_year(10)
    assert abs(s.net_worth - s.net_worth_real) < 1.0


def test_lock_cap_never_exceeded_in_sim(assumptions):
    a = assumptions  # noqa: F841
    cfg = build_twins(
        Profile(age=23, income_monthly=6_000_000, expense_monthly=3_000_000, savings=0),
        IncomeProfile("salary", 6_000_000),
        [
            Decision(
                type="loan_vs_save",
                loan=LoanDecision(kind="pinjol", amount=5_000_000, tenor_months=12, rate_daily=0.01),
                save=SaveDecision(monthly=0),
            )
        ],
        a.ruleset(),
        0.05,
        a.common,
    )
    loan_twin = next(t for t in cfg if t.code == "A")
    res = simulate(
        loan_twin,
        Profile(
            age=23,
            income_monthly=6_000_000,
            expense_monthly=3_000_000,
            savings=0,
            existing_debt=ExistingDebt(),
        ),
        IncomeProfile("salary", 6_000_000),
        a.preset("moderat"),
        a.ruleset(),
        months=60,
    )
    # Beban tidak boleh melebihi 100% pokok -> total dibayar <= 2x pokok
    total_paid = sum(m.paid_debt for m in res.months)
    assert total_paid <= 2 * 5_000_000 + 1e-3


def test_study_twin_behind_at_year2(assumptions):
    a = assumptions  # noqa: F841
    profile = Profile(age=23, income_monthly=6_000_000, expense_monthly=3_500_000, savings=10_000_000)
    decisions = [
        Decision(
            type="study_vs_work",
            study=StudyDecision(years=2, total_cost=80_000_000, part_time_work=False, salary_premium=0.15),
            work=WorkDecision(upskill_monthly=300_000, skill_premium=0.10, premium_after_months=12),
        )
    ]
    twins = build_twins(profile, IncomeProfile("salary", 6_000_000), decisions, a.ruleset(), 0.05, a.common)
    c = next(t for t in twins if t.code == "C")
    d = next(t for t in twins if t.code == "D")
    rc = simulate(c, profile, IncomeProfile("salary", 6_000_000), a.preset("moderat"), a.ruleset(), months=36)
    rd = simulate(d, profile, IncomeProfile("salary", 6_000_000), a.preset("moderat"), a.ruleset(), months=36)
    # Si Akademisi tertinggal di tahun ke-2
    assert rc.at_year(2).net_worth < rd.at_year(2).net_worth


def test_shock_income_loss_reduces_cash(assumptions):
    a = assumptions  # noqa: F841
    cfg = build_twins(
        Profile(age=23, income_monthly=6_000_000, expense_monthly=3_000_000, savings=20_000_000),
        IncomeProfile("salary", 6_000_000),
        [],
        a.ruleset(),
        0.05,
        a.common,
    )[0]
    base = simulate(
        cfg,
        Profile(age=23, income_monthly=6_000_000, expense_monthly=3_000_000, savings=20_000_000),
        IncomeProfile("salary", 6_000_000),
        a.preset("moderat"),
        a.ruleset(),
        months=24,
    )
    shock = Shock("income_loss_3m", "x", start_month=6, income_multiplier=0.0, duration_months=3)
    stressed = simulate(
        cfg,
        Profile(age=23, income_monthly=6_000_000, expense_monthly=3_000_000, savings=20_000_000),
        IncomeProfile("salary", 6_000_000),
        a.preset("moderat"),
        a.ruleset(),
        months=24,
        shock=shock,
    )
    assert stressed.at_month(8).cash < base.at_month(8).cash


def test_pinjol_dsr_flags_in_full_sim(assumptions):
    req = SimulationRequest(
        profile=Profile(age=23, income_monthly=3_000_000, expense_monthly=1_500_000, savings=0),
        decisions=[
            Decision(
                type="loan_vs_save",
                loan=LoanDecision(kind="pinjol", amount=4_000_000, tenor_months=3, rate_daily=0.003),
                save=SaveDecision(monthly=200_000),
            )
        ],
        preset="moderat",
    )
    full = run_full_simulation(req, assumptions)
    assert any(f["code"] == "DSR_OVER_30" for f in full.input_flags)


def test_full_sim_has_baseline_plus_two(assumptions):
    req = SimulationRequest(
        profile=Profile(age=23, income_monthly=6_000_000, expense_monthly=3_000_000, savings=5_000_000),
        decisions=[
            Decision(
                type="loan_vs_save",
                loan=LoanDecision(kind="pinjol", amount=2_000_000, tenor_months=3, rate_daily=0.003),
                save=SaveDecision(monthly=500_000),
            )
        ],
    )
    full = run_full_simulation(req, assumptions)
    codes = [t.cfg.code for t in full.twins]
    assert codes == ["0", "A", "B"]


def test_two_decisions_four_twins(assumptions):
    req = SimulationRequest(
        profile=Profile(age=23, income_monthly=6_000_000, expense_monthly=3_000_000, savings=5_000_000),
        decisions=[
            Decision(
                type="loan_vs_save",
                loan=LoanDecision(kind="pinjol", amount=2_000_000, tenor_months=3, rate_daily=0.003),
                save=SaveDecision(monthly=500_000),
            ),
            Decision(
                type="study_vs_work",
                study=StudyDecision(years=2, total_cost=80_000_000, salary_premium=0.15),
                work=WorkDecision(),
            ),
        ],
    )
    full = run_full_simulation(req, assumptions)
    codes = [t.cfg.code for t in full.twins]
    assert codes == ["0", "A", "B", "C", "D"]


def test_emergency_vs_invest_twins(assumptions):
    req = SimulationRequest(
        profile=Profile(
            age=28,
            income_monthly=8_000_000,
            expense_monthly=5_000_000,
            dependents_monthly=1_500_000,
            savings=2_000_000,
        ),
        decisions=[
            Decision(
                type="emergency_vs_invest",
                emergency=EmergencyDecision(target_months=6, invest_monthly=1_000_000),
            )
        ],
    )
    full = run_full_simulation(req, assumptions)
    codes = [t.cfg.code for t in full.twins]
    assert codes == ["0", "E", "F"]
    e = next(t for t in full.twins if t.cfg.code == "E")
    f = next(t for t in full.twins if t.cfg.code == "F")
    # Si Siaga punya dana darurat lebih tinggi awal
    assert e.summary["min_emergency_months"] >= f.summary["min_emergency_months"]


def test_variable_income_uses_min_for_stress(assumptions):
    a = assumptions  # noqa: F841
    profile = Profile(
        age=26,
        income_type="variable",
        income_monthly=5_500_000,
        expense_monthly=3_000_000,
        savings=5_000_000,
    )
    from app.schemas.input import IncomeRange

    profile.income_range = IncomeRange(min=4_000_000, max=7_000_000)
    ip = IncomeProfile("variable", 5_500_000, 4_000_000, 7_000_000)
    assert ip.base == 5_500_000
    assert ip.base_min == 4_000_000


def test_kpr_vs_rent_twins():
    from app.engine.regulatory import ruleset_from_assumptions
    from app.engine.simulator import simulate
    from app.engine.templates import twins_for_decision
    from app.schemas.input import Decision, KprDecision, Profile, RentDecision

    prof = Profile(
        age=30,
        income_type="salary",
        income_monthly=15_000_000,
        expense_monthly=5_000_000,
        dependents_monthly=1_000_000,
        savings=120_000_000,
    )
    ip = IncomeProfile("salary", 15_000_000)
    rs = ruleset_from_assumptions(None)
    dec = Decision(
        type="kpr_vs_rent",
        kpr=KprDecision(
            property_price=400_000_000,
            down_payment_pct=0.20,
            interest_rate_annual=0.08,
            tenor_years=15,
            property_appreciation_annual=0.04,
        ),
        rent=RentDecision(
            rent_monthly=2_000_000,
            invest_instrument="bond",
        ),
    )
    twins = twins_for_decision(dec, prof, ip, rs, 0.05, {})
    assert len(twins) == 2
    g, h = twins[0], twins[1]
    assert g.code == "G"
    assert g.initial_dp == 80_000_000
    assert g.property_initial_value == 400_000_000
    assert g.loan is not None
    assert g.loan.principal == 320_000_000

    assert h.code == "H"
    assert h.rent_monthly == 2_000_000
    assert h.monthly_invest > 0

    res_g = simulate(g, prof, ip, {"inflation": 0.03, "returns": {"bond": 0.068}}, rs, months=120)
    res_h = simulate(h, prof, ip, {"inflation": 0.03, "returns": {"bond": 0.068}}, rs, months=120)

    assert res_g.at_year(10).net_worth > 0
    assert res_h.at_year(10).net_worth > 0


def test_compute_milestones():
    from app.engine.simulator import MonthSnapshot, SimResult, compute_milestones
    from app.engine.templates import TwinConfig

    cfg = TwinConfig(code="0", label="Test")
    res = SimResult(config=cfg)
    for m in range(25):
        nw = m * 5_000_000  # reaches 100M at m=20
        debt = max(0.0, 10_000_000.0 - m * 2_000_000.0)  # debt=0 at m=5
        cash = m * 2_000_000.0  # reaches 6M at m=3
        res.months.append(
            MonthSnapshot(
                month=m,
                income=10_000_000,
                living=2_000_000,
                paid_debt=500_000,
                cash=cash,
                invest=0.0,
                debt=debt,
                net_worth=nw,
                net_worth_real=nw,
                cashflow=1_000_000,
                emergency_months=cash / 2_000_000,
                dsr=0.1,
                defaulted=False,
            )
        )
    milestones = compute_milestones(res, base_expense=2_000_000, emergency_target_months=3.0)
    assert milestones["emergency_fund_full"] == 3
    assert milestones["debt_free"] == 5
    assert milestones["net_worth_100m"] == 20
    assert milestones["net_worth_1b"] is None


def test_vehicle_lease_vs_cash():
    from app.engine.regulatory import ruleset_from_assumptions
    from app.engine.templates import twins_for_decision
    from app.schemas.input import VehicleCashDecision, VehicleLeaseDecision

    prof = Profile(
        age=24,
        income_type="salary",
        income_monthly=8_000_000,
        expense_monthly=4_000_000,
        dependents_monthly=0,
        savings=20_000_000,
        existing_debt=ExistingDebt(),
    )
    ip = IncomeProfile("salary", 8_000_000)
    rs = ruleset_from_assumptions(None)
    dec = Decision(
        type="vehicle_lease_vs_cash",
        vehicle_lease=VehicleLeaseDecision(
            vehicle_price=25_000_000,
            down_payment_pct=0.20,
            interest_rate_annual=0.12,
            tenor_months=36,
            depreciation_annual=0.12,
        ),
        vehicle_cash=VehicleCashDecision(
            used_vehicle_price=10_000_000,
            invest_instrument="stock",
        ),
    )
    twins = twins_for_decision(dec, prof, ip, rs, 0.05, {})
    assert len(twins) == 2
    twin_i, twin_j = twins[0], twins[1]
    assert twin_i.code == "I"
    assert twin_i.initial_dp == 5_000_000
    assert twin_i.loan is not None
    assert twin_i.loan.principal == 20_000_000

    assert twin_j.code == "J"
    assert twin_j.initial_dp == 10_000_000
    assert twin_j.loan is None
    assert twin_j.monthly_invest > 0

    res_i = simulate(twin_i, prof, ip, {"inflation": 0.03, "returns": {"stock": 0.10}}, rs, months=60)
    res_j = simulate(twin_j, prof, ip, {"inflation": 0.03, "returns": {"stock": 0.10}}, rs, months=60)

    assert res_i.at_year(3).net_worth > 0
    assert res_j.at_year(3).net_worth > 0


def test_wedding_grand_vs_intimate(assumptions):
    from app.engine.regulatory import ruleset_from_assumptions
    from app.schemas.input import WeddingGrandDecision, WeddingIntimateDecision

    prof = Profile(
        age=26,
        income_type="salary",
        income_monthly=12_000_000,
        expense_monthly=5_000_000,
        dependents_monthly=0,
        savings=60_000_000,
        existing_debt=ExistingDebt(),
    )
    ip = IncomeProfile("salary", 12_000_000)
    rs = ruleset_from_assumptions(None)
    dec = Decision(
        type="wedding_grand_vs_intimate",
        wedding_grand=WeddingGrandDecision(
            reception_cost=150_000_000,
            savings_used=50_000_000,
            loan_amount=100_000_000,
            interest_rate_annual=0.12,
            tenor_months=36,
        ),
        wedding_intimate=WeddingIntimateDecision(
            intimate_cost=25_000_000,
            invest_instrument="stock",
        ),
    )
    twins = twins_for_decision(dec, prof, ip, rs, 0.05, {})
    assert len(twins) == 2
    twin_k, twin_l = twins[0], twins[1]
    assert twin_k.code == "K"
    assert twin_k.initial_dp == 50_000_000
    assert twin_k.loan is not None
    assert twin_k.loan.principal == 100_000_000

    assert twin_l.code == "L"
    assert twin_l.initial_dp == 25_000_000
    assert twin_l.loan is None
    assert twin_l.monthly_invest > 0

    res_k = simulate(twin_k, prof, ip, {"inflation": 0.03, "returns": {"stock": 0.10}}, rs, months=60)
    res_l = simulate(twin_l, prof, ip, {"inflation": 0.03, "returns": {"stock": 0.10}}, rs, months=60)

    # Si Intim harus jauh lebih kaya dibanding Si Pesta yang terbebani cicilan KTA
    assert res_l.at_year(3).net_worth > res_k.at_year(3).net_worth


