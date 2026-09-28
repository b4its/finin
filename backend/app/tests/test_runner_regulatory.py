"""Test OJK Guard input: cakupan DSR untuk SEMUA template berpinjaman.

Regression guard: template properti sewa dan kendaraan (EV/ICE) sebelumnya
melewati pemeriksaan DSR. Test ini memastikan setiap template berpinjaman
memunculkan bendera DSR_OVER_30 ketika rasio cicilan melampaui batas OJK.
"""

from __future__ import annotations

from app.engine.assumptions import load_assumptions
from app.engine.regulatory import cap_for, check_dsr, check_pinjol, ruleset_from_assumptions
from app.engine.runner import regulatory_flags_for_input
from app.schemas.input import (
    Decision,
    DividendInvestDecision,
    EvVehicleDecision,
    IceVehicleDecision,
    Profile,
    RentalPropertyDecision,
)


def _ruleset() -> dict:
    return load_assumptions().ruleset()


def _profile(income: float = 3_000_000) -> Profile:
    # Penghasilan kecil agar hampir semua cicilan melampaui DSR 30%.
    return Profile(
        age=30,
        income_type="salary",
        income_monthly=income,
        expense_monthly=2_000_000,
    )


def _codes(flags: list[dict]) -> set[str]:
    return {f["code"] for f in flags}


def _rental(price: float = 1_500_000_000, dp: float = 0.20) -> Decision:
    return Decision(
        type="rental_property_vs_dividend",
        rental_property=RentalPropertyDecision(property_price=price, down_payment_pct=dp),
        dividend_invest=DividendInvestDecision(),
    )


def _ev_ice(
    ev_price: float = 400_000_000,
    ice_price: float = 300_000_000,
    ev_subsidy: float = 0,
) -> Decision:
    # Template ini butuh keduanya; DSR dihitung dari masing-masing pinjaman.
    return Decision(
        type="electric_vehicle_vs_ice",
        ev_vehicle=EvVehicleDecision(
            vehicle_price=ev_price,
            government_subsidy=ev_subsidy,
            loan_tenor_months=12,
        ),
        ice_vehicle=IceVehicleDecision(vehicle_price=ice_price, loan_tenor_months=12),
    )


def test_rental_property_kpr_triggers_dsr_flag():
    """Gap sebelumnya: properti sewa (KPR) tidak diperiksa DSR."""
    flags = regulatory_flags_for_input(_profile(), [_rental()], _ruleset())
    assert "DSR_OVER_30" in _codes(flags)
    assert any("properti sewa" in f["msg"] for f in flags if f["code"] == "DSR_OVER_30")


def test_ev_vehicle_loan_triggers_dsr_flag():
    """Gap sebelumnya: kredit kendaraan listrik (EV) tidak diperiksa DSR."""
    flags = regulatory_flags_for_input(_profile(), [_ev_ice()], _ruleset())
    assert "DSR_OVER_30" in _codes(flags)
    assert any("listrik" in f["msg"] for f in flags if f["code"] == "DSR_OVER_30")


def test_ice_vehicle_loan_triggers_dsr_flag():
    """Gap sebelumnya: kredit kendaraan bensin (ICE) tidak diperiksa DSR."""
    flags = regulatory_flags_for_input(_profile(), [_ev_ice()], _ruleset())
    assert "DSR_OVER_30" in _codes(flags)
    assert any("bensin" in f["msg"] for f in flags if f["code"] == "DSR_OVER_30")


def test_safe_income_no_dsr_flag_for_rental_property():
    """Penghasilan besar + DP tinggi -> tidak ada bendera DSR (guard tidak over-trigger)."""
    dec = _rental(price=500_000_000, dp=0.50)
    flags = regulatory_flags_for_input(_profile(income=200_000_000), [dec], _ruleset())
    assert "DSR_OVER_30" not in _codes(flags)


def test_zero_income_no_dsr_flag():
    """Tanpa penghasilan, DSR tidak bisa dihitung -> tidak ada bendera DSR."""
    flags = regulatory_flags_for_input(_profile(income=0), [_ev_ice()], _ruleset())
    assert "DSR_OVER_30" not in _codes(flags)


def test_distinct_loans_produce_distinct_flags():
    """Dua keputusan berpinjaman berbeda menghasilkan bendera DSR terpisah (bukan dedup jadi satu)."""
    decs = [_ev_ice(), _rental()]
    flags = regulatory_flags_for_input(_profile(), decs, _ruleset())
    dsr_flags = [f for f in flags if f["code"] == "DSR_OVER_30"]
    # EV + ICE (2) + properti sewa (1) = 3 bendera terpisah.
    assert len(dsr_flags) >= 3
    msgs = " ".join(f["msg"] for f in dsr_flags)
    assert "listrik" in msgs and "bensin" in msgs and "properti sewa" in msgs


def test_ruleset_missing_dsr_cap_no_keyerror():
    """Ruleset tanpa dsr_cap tidak boleh menyebabkan KeyError."""
    rs = ruleset_from_assumptions(
        {"consumer_caps": [{"tenor_max_months": None, "rate_daily_max": 0.002, "penalty_daily_max": 0.002}]}
    )
    rs.pop("dsr_cap", None)
    # Tidak boleh melempar.
    flags = regulatory_flags_for_input(_profile(), [_ev_ice()], rs)
    assert isinstance(flags, list)


def test_fully_subsidized_ev_does_not_attribute_existing_debt_to_ev():
    """EV tanpa pokok kredit tidak boleh menghasilkan bendera atas nama kredit EV."""
    profile = _profile(income=3_000_000)
    profile.existing_debt.monthly_payment = 2_000_000
    dec = _ev_ice(ev_price=100_000_000, ev_subsidy=100_000_000)
    flags = regulatory_flags_for_input(profile, [dec], _ruleset())
    assert not any("listrik" in f["msg"] for f in flags if f["code"] == "DSR_OVER_30")


def test_regulatory_helpers_fallback_without_dsr_cap():
    """Helper publik memakai batas default ketika ruleset parsial diberikan."""
    rs = {"consumer_caps": [(None, 0.002, 0.002)], "lock_cap_ratio": 1.0}
    assert check_dsr(100_000, 200_000, rs) is not None
    assert any(
        flag.code == "DSR_OVER_30"
        for flag in check_pinjol(1_000_000, 12, 0.001, 200_000, ruleset=rs)
    )


def test_cap_for_handles_partial_unsorted_ruleset():
    """Cap dipilih berdasarkan tenor meski input tidak berurutan dan tanpa catch-all."""
    rs = {"consumer_caps": [(24, 0.001, 0.001), (6, 0.003, 0.003)]}
    assert cap_for(3, rs) == (0.003, 0.003)
    assert cap_for(12, rs) == (0.001, 0.001)
    assert cap_for(36, rs) == (0.001, 0.001)
    assert cap_for(3, {"consumer_caps": []}) == cap_for(3)
