"""Orkestrator engine: dari input -> twin hasil lengkap + skor + robust."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.assumptions import Assumptions, load_assumptions
from app.engine.income import IncomeProfile
from app.engine.regulatory import Flag, check_dsr, check_pinjol, slik_flag
from app.engine.scoring import rank_twins
from app.engine.sensitivity import run_sensitivity
from app.engine.shocks import run_stress
from app.engine.simulator import SimResult, simulate, summary, yearly_series
from app.engine.templates import TwinConfig, build_twins
from app.schemas.input import Decision, Profile, SimulationRequest


@dataclass
class TwinResult:
    cfg: TwinConfig
    result: SimResult
    series: list[dict]
    summary: dict
    flags: list[dict]
    stress: list[dict]
    score: float
    score_breakdown: dict
    deleted_by_hard_rule: bool = False


@dataclass
class FullSimulation:
    twins: list[TwinResult]
    robust: bool
    robust_reason: str
    preset_winners: dict[str, str]
    preset_scores: dict[str, dict[str, float]]
    input_flags: list[dict]
    assumptions: Assumptions
    preset: str
    horizon_months: int
    best_twin: str = "0"
    sensitivity_drivers: list[str] = field(default_factory=list)
    effective_values: dict = field(default_factory=dict)
    overrides: dict = field(default_factory=dict)


def income_profile_from(profile: Profile) -> IncomeProfile:
    return IncomeProfile(
        income_type=profile.income_type,
        income_monthly=profile.income_monthly,
        income_min=profile.income_range.min if profile.income_range else None,
        income_max=profile.income_range.max if profile.income_range else None,
    )


def _loan_dsr_flag(
    label: str,
    scheduled_payment: float,
    existing_payment: float,
    income_monthly: float,
    ruleset: dict,
) -> Flag | None:
    """Bendera oranye DSR untuk satu cicilan pinjaman baru + cicilan berjalan.

    Mengembalikan None bila penghasilan tidak diketahui (<=0) atau rasio aman.
    """
    if income_monthly <= 0:
        return None
    total = scheduled_payment + existing_payment
    dsr = total / income_monthly
    dsr_cap = ruleset.get("dsr_cap", 0.30)
    if dsr > dsr_cap + 1e-12:
        return Flag(
            "orange",
            "DSR_OVER_30",
            f"Cicilan {label} Rp{total:,.0f}/bulan ≈ {dsr:.0%} penghasilan, "
            f"melebihi batas kemampuan bayar OJK {dsr_cap:.0%}.",
        )
    return None


def _annuity_loan(principal: float, tenor_months: float, annual_rate: float, ruleset: dict, kind: str = "annuity"):
    """Buat objek Loan annuity untuk pengecekan DSR (import lokal agar ringan).

    ``tenor_months`` datang sebagai float dari perhitungan (mis. ``tenor_years * 12``);
    tenor adalah satuan bulan bulat, jadi dibulatkan ke int terdekat agar konsisten
    dengan tipe ``Loan.tenor_months``.
    """
    from app.engine.loans import Loan

    return Loan(
        kind=kind,
        principal=principal,
        tenor_months=round(tenor_months),
        annual_rate=annual_rate,
        ruleset=ruleset,
    )


def _loan_checks_for(dec: Decision, ruleset: dict) -> list[tuple[str, float]]:
    """Kembalikan daftar (label, cicilan_bulanan) untuk setiap pinjaman pada satu keputusan.

    Satu sumber kebenaran untuk SEMUA template yang mengandung pinjaman agar
    OJK Guard tidak melewatkan template (mis. properti sewa & kendaraan EV/ICE).
    """
    checks: list[tuple[str, float]] = []

    if dec.type == "kpr_vs_rent" and dec.kpr is not None:
        dp = dec.kpr.property_price * dec.kpr.down_payment_pct
        loan = _annuity_loan(
            dec.kpr.property_price - dp,
            dec.kpr.tenor_years * 12,
            dec.kpr.interest_rate_annual,
            ruleset,
            kind="kpr",
        )
        checks.append(("KPR", loan.scheduled_payment))

    if dec.type == "vehicle_lease_vs_cash" and dec.vehicle_lease is not None:
        vl = dec.vehicle_lease
        dp = vl.vehicle_price * vl.down_payment_pct
        loan = _annuity_loan(
            vl.vehicle_price - dp, vl.tenor_months, vl.interest_rate_annual, ruleset
        )
        checks.append(("kredit kendaraan", loan.scheduled_payment))

    if (
        dec.type == "wedding_grand_vs_intimate"
        and dec.wedding_grand is not None
        and dec.wedding_grand.loan_amount > 0
    ):
        wg = dec.wedding_grand
        loan = _annuity_loan(
            wg.loan_amount, wg.tenor_months, wg.interest_rate_annual, ruleset
        )
        checks.append(("KTA resepsi pernikahan", loan.scheduled_payment))

    if (
        dec.type == "franchise_vs_passive_invest"
        and dec.franchise is not None
        and dec.franchise.kur_loan_amount > 0
    ):
        fr = dec.franchise
        loan = _annuity_loan(
            fr.kur_loan_amount, fr.kur_tenor_months, fr.kur_interest_rate_annual, ruleset
        )
        checks.append(("pinjaman KUR waralaba", loan.scheduled_payment))

    if (
        dec.type == "haji_furoda_vs_reguler"
        and dec.haji_furoda is not None
        and dec.haji_furoda.financing_amount > 0
    ):
        hf = dec.haji_furoda
        loan = _annuity_loan(
            hf.financing_amount, hf.tenor_months, hf.financing_rate_annual, ruleset
        )
        checks.append(("pembiayaan haji khusus", loan.scheduled_payment))

    # --- Gap yang sebelumnya terlewat: properti sewa (KPR) ---
    if dec.type == "rental_property_vs_dividend" and dec.rental_property is not None:
        rp = dec.rental_property
        dp = rp.property_price * rp.down_payment_pct
        loan = _annuity_loan(
            rp.property_price - dp,
            rp.kpr_tenor_years * 12,
            rp.kpr_interest_rate_annual,
            ruleset,
            kind="kpr",
        )
        checks.append(("KPR properti sewa", loan.scheduled_payment))

    # --- Gap yang sebelumnya terlewat: kendaraan listrik (EV) ---
    if dec.type == "electric_vehicle_vs_ice" and dec.ev_vehicle is not None:
        ev = dec.ev_vehicle
        price_after_subsidy = max(0.0, ev.vehicle_price - ev.government_subsidy)
        dp = price_after_subsidy * ev.down_payment_pct
        principal = price_after_subsidy - dp
        if principal > 0:
            loan = _annuity_loan(
                principal, ev.loan_tenor_months, ev.loan_interest_rate_annual, ruleset
            )
            checks.append(("kredit kendaraan listrik", loan.scheduled_payment))

    # --- Gap yang sebelumnya terlewat: kendaraan bensin (ICE) ---
    if dec.type == "electric_vehicle_vs_ice" and dec.ice_vehicle is not None:
        ice = dec.ice_vehicle
        dp = ice.vehicle_price * ice.down_payment_pct
        loan = _annuity_loan(
            ice.vehicle_price - dp, ice.loan_tenor_months, ice.loan_interest_rate_annual, ruleset
        )
        checks.append(("kredit kendaraan bensin", loan.scheduled_payment))

    return checks


def regulatory_flags_for_input(profile: Profile, decisions: list[Decision], ruleset: dict) -> list[dict]:
    """Bendera dari wizard (F4): pinjol & DSR untuk SEMUA template berpinjaman.

    Loop tabel-driven lewat ``_loan_checks_for`` sehingga setiap template yang
    mengandung pinjaman (KPR, properti sewa, kendaraan lease/EV/ICE, KTA, KUR,
    pembiayaan haji) selalu diperiksa DSR-nya — tidak ada lagi template yang lolos.
    """
    flags: list[Flag] = []
    existing = profile.existing_debt.monthly_payment
    income = profile.income_monthly

    for dec in decisions:
        # Pinjol/paylater punya aturan bunga+denda tersendiri.
        if dec.type == "loan_vs_save" and dec.loan is not None:
            flags.extend(
                check_pinjol(
                    amount=dec.loan.amount,
                    tenor_months=dec.loan.tenor_months,
                    rate_daily=dec.loan.rate_daily,
                    income_monthly=income,
                    existing_payment=existing,
                    penalty_daily=dec.loan.penalty_daily,
                    ruleset=ruleset,
                )
            )
        # DSR untuk seluruh pinjaman annuity (single source of truth).
        for label, installment in _loan_checks_for(dec, ruleset):
            f = _loan_dsr_flag(label, installment, existing, income, ruleset)
            if f:
                flags.append(f)

    # DSR utang berjalan (tanpa keputusan baru).
    if income > 0 and existing > 0:
        f = check_dsr(existing, income, ruleset)
        if f:
            flags.append(f)

    # Deduplikasi berdasarkan (code, msg) — kode sama dengan pesan berbeda
    # (mis. dua pinjaman berbeda) tetap ditampilkan agar pengguna tahu sumbernya.
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for f in flags:
        key = (f.code, f.msg)
        if key in seen:
            continue
        seen.add(key)
        out.append(f.to_dict())
    return out


def _merge_preset(assumptions: Assumptions, preset: str, overrides: dict) -> dict:
    merged = assumptions.preset(preset)
    if overrides:
        for k, v in overrides.items():
            if k == "returns" and isinstance(v, dict):
                merged.setdefault("returns", {}).update(v)
            else:
                merged[k] = v
    return merged


def run_full_simulation(request: SimulationRequest, assumptions: Assumptions | None = None) -> FullSimulation:
    a = assumptions or load_assumptions()
    ruleset = a.ruleset()
    profile = request.profile
    income_profile = income_profile_from(profile)
    merged = _merge_preset(a, request.preset, request.assumption_overrides)
    growth = merged.get("salary_growth", 0.05)
    common = a.common

    # 1. Bangun twin
    twins_cfg = build_twins(profile, income_profile, request.decisions, ruleset, growth, common)

    # 2. Simulasi tiap twin (preset terpilih)
    results: dict[str, SimResult] = {}
    for cfg in twins_cfg:
        results[cfg.code] = simulate(
            cfg, profile, income_profile, merged, ruleset, months=request.horizon_months
        )

    # 3. Stress test
    stress_map: dict[str, list[dict]] = {}
    stress_bool: dict[str, bool] = {}
    for cfg in twins_cfg:
        st = run_stress(cfg, profile, income_profile, a, ruleset, months=request.horizon_months)
        stress_map[cfg.code] = st
        stress_bool[cfg.code] = all(x["survived"] for x in st) if st else True

    # 4. Sensitivitas 3 preset
    sens = run_sensitivity(twins_cfg, profile, income_profile, a, ruleset, months=request.horizon_months)
    preset_wins = {c: 0 for c in results}
    for _, w in sens["preset_winners"].items():
        if w in preset_wins:
            preset_wins[w] += 1

    # 5. Ranking & skor
    best, breakdowns = rank_twins(results, stress_bool, preset_wins, dsr_cap=ruleset.get("dsr_cap", 0.30))

    # 6. Rakit hasil
    twin_results: list[TwinResult] = []
    input_flags = regulatory_flags_for_input(profile, request.decisions, ruleset)
    base_expense = profile.expense_monthly + profile.dependents_monthly
    for cfg in twins_cfg:
        res = results[cfg.code]
        summ = summary(res, base_expense=base_expense)
        # Bendera tingkat-twin hanya untuk twin yang benar-benar mengambil pinjaman.
        # Bendera input (mis. DSR dari pinjol di template) tampil di level simulasi.
        flags: list[dict] = []
        if cfg.loan is not None:
            flags.extend(
                [
                    f.to_dict()
                    for f in check_pinjol(
                        amount=cfg.loan.principal,
                        tenor_months=cfg.loan.tenor_months,
                        rate_daily=cfg.loan.rate_daily,
                        income_monthly=profile.income_monthly,
                        existing_payment=profile.existing_debt.monthly_payment,
                        penalty_daily=cfg.loan.penalty_daily,
                        ruleset=ruleset,
                    )
                ]
            )
        if res.defaulted_months > 0:
            flags.append(slik_flag().to_dict())
        # dedup flags
        seen: set[tuple[str, str]] = set()
        uniq: list[dict] = []
        for f in flags:
            key = (str(f["code"]), str(f["level"]))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(f)

        bd = breakdowns.get(cfg.code, {})
        twin_results.append(
            TwinResult(
                cfg=cfg,
                result=res,
                series=yearly_series(res, max_year=min(request.horizon_months // 12, 20)),
                summary=summ,
                flags=uniq,
                stress=stress_map.get(cfg.code, []),
                score=bd.get("total", 0.0),
                score_breakdown=bd,
                deleted_by_hard_rule=bool(bd.get("deleted_by_hard_rule", False)),
            )
        )

    # Simpan skor per preset juga di breakdown agar bisa ditampilkan.
    for tr in twin_results:
        tr.score_breakdown["preset_scores"] = sens["preset_scores"].get(tr.cfg.code, {})

    return FullSimulation(
        twins=twin_results,
        robust=sens["robust"],
        robust_reason=sens["robust_reason"],
        preset_winners=sens["preset_winners"],
        preset_scores=sens["preset_scores"],
        input_flags=input_flags,
        assumptions=a,
        preset=request.preset,
        horizon_months=request.horizon_months,
        best_twin=best,
        sensitivity_drivers=sens.get("drivers", []),
        effective_values=merged,
        overrides=dict(request.assumption_overrides or {}),
    )
