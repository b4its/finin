"""Template keputusan -> twin (ceteris paribus: hanya 1 variabel yang berubah).

Setiap keputusan menghasilkan 2 twin (A/B atau C/D atau E/F).
Twin 0 "Kamu Tanpa Perubahan" adalah baseline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.engine.income import IncomeProfile
from app.engine.loans import Loan
from app.schemas.input import Decision, Profile

# Warna & pola sesuai PRD §11
TWIN_STYLE = {
    "0": {"color": "#94A3B8", "dash": "solid", "icon": "circle-dashed"},
    "A": {"color": "#F97362", "dash": "dashed", "icon": "credit-card"},
    "B": {"color": "#34D399", "dash": "dotted", "icon": "piggy-bank"},
    "C": {"color": "#818CF8", "dash": "dashdot", "icon": "graduation-cap"},
    "D": {"color": "#FBBF24", "dash": "longdash", "icon": "briefcase"},
    "E": {"color": "#22D3EE", "dash": "solid", "icon": "shield"},
    "F": {"color": "#C084FC", "dash": "dashed", "icon": "trending-up"},
    "G": {"color": "#10B981", "dash": "solid", "icon": "home"},
    "H": {"color": "#EC4899", "dash": "dashed", "icon": "key"},
    "I": {"color": "#F97316", "dash": "solid", "icon": "car"},
    "J": {"color": "#06B6D4", "dash": "dashed", "icon": "bike"},
    "K": {"color": "#E11D48", "dash": "solid", "icon": "party"},
    "L": {"color": "#14B8A6", "dash": "dashed", "icon": "gem"},
    "M": {"color": "#8B5CF6", "dash": "solid", "icon": "store"},
    "N": {"color": "#10B981", "dash": "dashed", "icon": "trending-up"},
    "O": {"color": "#F43F5E", "dash": "solid", "icon": "shield-alert"},
    "P": {"color": "#059669", "dash": "dashed", "icon": "graduation-cap"},
}

STYLE_FALLBACK = {"color": "#94A3B8", "dash": "solid", "icon": "circle"}


@dataclass
class TwinConfig:
    """Konfigurasi lengkap satu twin untuk simulator."""

    code: str
    label: str
    description: str = ""
    color: str = STYLE_FALLBACK["color"]
    dash: str = STYLE_FALLBACK["dash"]
    icon: str = STYLE_FALLBACK["icon"]

    # pinjaman yang diambil twin ini (selain utang berjalan)
    loan: Loan | None = None
    # dana darurat: twin ini menabung untuk itu dulu?
    emergency_first: bool = False
    emergency_target_months: int = 6
    # kontribusi menabung/investasi bulanan tetap
    monthly_invest: float = 0.0
    instrument: str = "money_market"
    # jalur penghasilan
    study: bool = False
    graduate_month: int | None = None
    part_time_monthly: float = 0.0
    post_graduate_multiplier: float = 1.0
    skill_month: int | None = None
    skill_multiplier: float = 1.0
    # laba usaha sampingan/waralaba bulanan
    business_profit_monthly: float = 0.0
    # biaya kuliah (dibayar bulanan)
    study_cost: float = 0.0
    # biaya kursus bulanan
    upskill_monthly: float = 0.0
    # properti & KPR vs sewa
    property_initial_value: float = 0.0
    property_appreciation_annual: float = 0.0
    initial_dp: float = 0.0
    rent_monthly: float = 0.0
    # kendaraan kredit vs tunai
    vehicle_initial_value: float = 0.0
    vehicle_depreciation_annual: float = 0.0
    # pendidikan anak: asuransi jiwa murni vs unitlink PAYDI
    insurance_monthly: float = 0.0
    unitlink_monthly_premium: float = 0.0
    unitlink_acq_y1: float = 0.60
    unitlink_acq_y2: float = 0.30
    unitlink_acq_y3: float = 0.15
    meta: dict[str, Any] = field(default_factory=dict)


def _style(code: str) -> dict:
    s = TWIN_STYLE.get(code, STYLE_FALLBACK)
    return {"color": s["color"], "dash": s["dash"], "icon": s["icon"]}


def baseline_twin(
    profile: Profile,
    income_profile: IncomeProfile,
    ruleset: dict,
    *,
    monthly_invest: float = 0.0,
    instrument: str = "money_market",
) -> TwinConfig:
    st = _style("0")
    return TwinConfig(
        code="0",
        label="Kamu Tanpa Perubahan",
        description="Baseline: semua keputusan tetap seperti sekarang, tanpa perubahan besar.",
        monthly_invest=monthly_invest,
        instrument=instrument,
        meta={"role": "baseline"},
        **st,
    )


def _loan_from_decision(dec: Decision, ruleset: dict) -> Loan:
    assert dec.loan is not None
    return Loan(
        kind=dec.loan.kind,
        principal=dec.loan.amount,
        tenor_months=dec.loan.tenor_months,
        rate_daily=dec.loan.rate_daily,
        penalty_daily=dec.loan.penalty_daily,
        ruleset=ruleset,
    )


def twins_for_decision(
    dec: Decision,
    profile: Profile,
    income_profile: IncomeProfile,
    ruleset: dict,
    growth_annual: float,
    common: dict,
) -> list[TwinConfig]:
    """Hasilkan 2 twin ceteris paribus dari satu keputusan."""

    if dec.type == "loan_vs_save":
        assert dec.loan is not None and dec.save is not None
        loan = _loan_from_decision(dec, ruleset)
        a_style = _style("A")
        b_style = _style("B")

        twin_a = TwinConfig(
            code="A",
            label="Si Cicilan",
            description=(
                f"Mengambil {dec.loan.kind} Rp{dec.loan.amount:,.0f} tenor {dec.loan.tenor_months} bulan "
                f"bunga {dec.loan.rate_daily:.2%}/hari."
            ),
            loan=loan,
            monthly_invest=0.0,
            meta={
                "kind": dec.loan.kind,
                "amount": dec.loan.amount,
                "tenor": dec.loan.tenor_months,
                "rate_daily": dec.loan.rate_daily,
            },
            **a_style,
        )
        twin_b = TwinConfig(
            code="B",
            label="Si Penabung",
            description=(
                f"Menahan diri dari {dec.loan.kind}, menabung Rp{dec.save.monthly:,.0f}/bulan "
                f"ke {dec.save.instrument}."
            ),
            monthly_invest=dec.save.monthly,
            instrument=dec.save.instrument,
            meta={"monthly": dec.save.monthly, "instrument": dec.save.instrument},
            **b_style,
        )
        return [twin_a, twin_b]

    if dec.type == "study_vs_work":
        assert dec.study is not None and dec.work is not None
        months_study = dec.study.years * 12
        c_style = _style("C")
        d_style = _style("D")

        twin_c = TwinConfig(
            code="C",
            label="Si Akademisi",
            description=(
                f"Lanjut S2 {dec.study.years} tahun, biaya total Rp{dec.study.total_cost:,.0f}, "
                f"premi gaji +{dec.study.salary_premium:.0%}"
                + (" (sambil kerja paruh waktu)." if dec.study.part_time_work else ".")
            ),
            study=True,
            graduate_month=months_study,
            part_time_monthly=dec.study.part_time_monthly if dec.study.part_time_work else 0.0,
            post_graduate_multiplier=1.0 + dec.study.salary_premium,
            study_cost=dec.study.total_cost / months_study if months_study else 0.0,
            monthly_invest=0.0,
            meta={
                "years": dec.study.years,
                "total_cost": dec.study.total_cost,
                "premium": dec.study.salary_premium,
                "part_time": dec.study.part_time_work,
            },
            **c_style,
        )
        twin_d = TwinConfig(
            code="D",
            label="Si Praktisi",
            description=(
                f"Kerja langsung + upskilling Rp{dec.work.upskill_monthly:,.0f}/bulan, "
                f"premi keahlian +{dec.work.skill_premium:.0%} setelah {dec.work.premium_after_months} bulan."
            ),
            upskill_monthly=dec.work.upskill_monthly,
            skill_month=dec.work.premium_after_months,
            skill_multiplier=1.0 + dec.work.skill_premium,
            meta={
                "upskill_monthly": dec.work.upskill_monthly,
                "skill_premium": dec.work.skill_premium,
                "premium_after": dec.work.premium_after_months,
            },
            **d_style,
        )
        return [twin_c, twin_d]

    if dec.type == "emergency_vs_invest":
        assert dec.emergency is not None
        e_style = _style("E")
        f_style = _style("F")
        twin_e = TwinConfig(
            code="E",
            label="Si Siaga",
            description=f"Mengumpulkan dana darurat {dec.emergency.target_months} bulan pengeluaran dulu sebelum investasi.",
            emergency_first=True,
            emergency_target_months=dec.emergency.target_months,
            monthly_invest=dec.emergency.invest_monthly,
            meta={"target_months": dec.emergency.target_months},
            **e_style,
        )
        twin_f = TwinConfig(
            code="F",
            label="Si Agresif",
            description=f"Langsung investasi Rp{dec.emergency.invest_monthly:,.0f}/bulan tanpa membangun dana darurat.",
            emergency_first=False,
            monthly_invest=dec.emergency.invest_monthly,
            meta={"invest_monthly": dec.emergency.invest_monthly},
            **f_style,
        )
        return [twin_e, twin_f]

    if dec.type == "kpr_vs_rent":
        assert dec.kpr is not None and dec.rent is not None
        g_style = _style("G")
        h_style = _style("H")

        dp_amount = dec.kpr.property_price * dec.kpr.down_payment_pct
        loan_principal = dec.kpr.property_price - dp_amount
        tenor_months = dec.kpr.tenor_years * 12
        kpr_loan = Loan(
            kind="kpr",
            principal=loan_principal,
            tenor_months=tenor_months,
            annual_rate=dec.kpr.interest_rate_annual,
            ruleset=ruleset,
        )

        twin_g = TwinConfig(
            code="G",
            label="Si Pemilik Rumah",
            description=(
                f"Membeli rumah Rp{dec.kpr.property_price:,.0f} (DP {dec.kpr.down_payment_pct:.0%}, "
                f"KPR {dec.kpr.tenor_years} th bunga {dec.kpr.interest_rate_annual:.1%}/th)."
            ),
            loan=kpr_loan,
            property_initial_value=dec.kpr.property_price,
            property_appreciation_annual=dec.kpr.property_appreciation_annual,
            initial_dp=dp_amount,
            monthly_invest=0.0,
            meta={
                "property_price": dec.kpr.property_price,
                "dp_amount": dp_amount,
                "tenor_years": dec.kpr.tenor_years,
                "interest_rate": dec.kpr.interest_rate_annual,
            },
            **g_style,
        )

        invest_diff = max(0.0, kpr_loan.scheduled_payment - dec.rent.rent_monthly)
        twin_h = TwinConfig(
            code="H",
            label="Si Pengontrak & Investor",
            description=(
                f"Sewa rumah Rp{dec.rent.rent_monthly:,.0f}/bulan, menahan DP, dan investasi "
                f"selisih cicilan Rp{invest_diff:,.0f}/bulan ke {dec.rent.invest_instrument}."
            ),
            rent_monthly=dec.rent.rent_monthly,
            monthly_invest=invest_diff,
            instrument=dec.rent.invest_instrument,
            meta={
                "rent_monthly": dec.rent.rent_monthly,
                "monthly_invest": invest_diff,
                "instrument": dec.rent.invest_instrument,
            },
            **h_style,
        )
        return [twin_g, twin_h]

    if dec.type == "vehicle_lease_vs_cash":
        assert dec.vehicle_lease is not None and dec.vehicle_cash is not None
        i_style = _style("I")
        j_style = _style("J")

        dp_amount = dec.vehicle_lease.vehicle_price * dec.vehicle_lease.down_payment_pct
        principal = dec.vehicle_lease.vehicle_price - dp_amount
        lease_loan = Loan(
            kind="annuity",
            principal=principal,
            tenor_months=dec.vehicle_lease.tenor_months,
            annual_rate=dec.vehicle_lease.interest_rate_annual,
            ruleset=ruleset,
        )

        twin_i = TwinConfig(
            code="I",
            label="Si Pengkredit Leasing",
            description=(
                f"Beli kendaraan baru Rp{dec.vehicle_lease.vehicle_price:,.0f} via leasing OJK "
                f"(DP {dec.vehicle_lease.down_payment_pct:.0%}, tenor {dec.vehicle_lease.tenor_months} bln, "
                f"bunga {dec.vehicle_lease.interest_rate_annual:.1%}/th)."
            ),
            loan=lease_loan,
            vehicle_initial_value=dec.vehicle_lease.vehicle_price,
            vehicle_depreciation_annual=dec.vehicle_lease.depreciation_annual,
            initial_dp=dp_amount,
            monthly_invest=0.0,
            meta={
                "vehicle_price": dec.vehicle_lease.vehicle_price,
                "dp_amount": dp_amount,
                "tenor_months": dec.vehicle_lease.tenor_months,
                "interest_rate": dec.vehicle_lease.interest_rate_annual,
            },
            **i_style,
        )

        invest_diff = max(0.0, lease_loan.scheduled_payment)
        twin_j = TwinConfig(
            code="J",
            label="Si Pembeli Bekas & Investor",
            description=(
                f"Beli kendaraan bekas layak Rp{dec.vehicle_cash.used_vehicle_price:,.0f} tunai (bebas cicilan), "
                f"investasikan selisih cicilan Rp{invest_diff:,.0f}/bln ke {dec.vehicle_cash.invest_instrument}."
            ),
            vehicle_initial_value=dec.vehicle_cash.used_vehicle_price,
            vehicle_depreciation_annual=0.10,
            initial_dp=dec.vehicle_cash.used_vehicle_price,
            monthly_invest=invest_diff,
            instrument=dec.vehicle_cash.invest_instrument,
            meta={
                "used_vehicle_price": dec.vehicle_cash.used_vehicle_price,
                "monthly_invest": invest_diff,
                "instrument": dec.vehicle_cash.invest_instrument,
            },
            **j_style,
        )
        return [twin_i, twin_j]

    if dec.type == "wedding_grand_vs_intimate":
        assert dec.wedding_grand is not None and dec.wedding_intimate is not None
        k_style = _style("K")
        l_style = _style("L")

        kta_loan = None
        scheduled_pay = 0.0
        if dec.wedding_grand.loan_amount > 0:
            kta_loan = Loan(
                kind="annuity",
                principal=dec.wedding_grand.loan_amount,
                tenor_months=dec.wedding_grand.tenor_months,
                annual_rate=dec.wedding_grand.interest_rate_annual,
                ruleset=ruleset,
            )
            scheduled_pay = kta_loan.scheduled_payment

        loan_desc = (
            f" + KTA Rp{dec.wedding_grand.loan_amount:,.0f} tenor {dec.wedding_grand.tenor_months} bln)"
            if dec.wedding_grand.loan_amount > 0
            else ")"
        )
        twin_k = TwinConfig(
            code="K",
            label="Si Pesta Akbar",
            description=(
                f"Pesta pernikahan megah Rp{dec.wedding_grand.reception_cost:,.0f} "
                f"(tabungan Rp{dec.wedding_grand.savings_used:,.0f}{loan_desc}."
            ),
            loan=kta_loan,
            initial_dp=dec.wedding_grand.savings_used,
            monthly_invest=0.0,
            meta={
                "reception_cost": dec.wedding_grand.reception_cost,
                "savings_used": dec.wedding_grand.savings_used,
                "loan_amount": dec.wedding_grand.loan_amount,
                "tenor_months": dec.wedding_grand.tenor_months,
                "interest_rate": dec.wedding_grand.interest_rate_annual,
            },
            **k_style,
        )

        invest_diff = max(0.0, scheduled_pay)
        twin_l = TwinConfig(
            code="L",
            label="Si Intim & Modal Keluarga",
            description=(
                f"Pernikahan intim/KUA Rp{dec.wedding_intimate.intimate_cost:,.0f} tunai bebas utang, "
                f"investasikan selisih cicilan Rp{invest_diff:,.0f}/bln ke {dec.wedding_intimate.invest_instrument}."
            ),
            initial_dp=dec.wedding_intimate.intimate_cost,
            monthly_invest=invest_diff,
            instrument=dec.wedding_intimate.invest_instrument,
            meta={
                "intimate_cost": dec.wedding_intimate.intimate_cost,
                "monthly_invest": invest_diff,
                "instrument": dec.wedding_intimate.invest_instrument,
            },
            **l_style,
        )
        return [twin_k, twin_l]

    if dec.type == "franchise_vs_passive_invest":
        assert dec.franchise is not None and dec.passive_invest is not None
        m_style = _style("M")
        n_style = _style("N")

        kur_loan = None
        scheduled_pay = 0.0
        if dec.franchise.kur_loan_amount > 0:
            kur_loan = Loan(
                kind="annuity",
                principal=dec.franchise.kur_loan_amount,
                tenor_months=dec.franchise.kur_tenor_months,
                annual_rate=dec.franchise.kur_interest_rate_annual,
                ruleset=ruleset,
            )
            scheduled_pay = kur_loan.scheduled_payment

        loan_desc = (
            f" + KUR Rp{dec.franchise.kur_loan_amount:,.0f} tenor {dec.franchise.kur_tenor_months} bln)"
            if dec.franchise.kur_loan_amount > 0
            else ")"
        )
        twin_m = TwinConfig(
            code="M",
            label="Si Pebisnis Waralaba",
            description=(
                f"Buka franchise mikro Rp{dec.franchise.franchise_fee:,.0f} "
                f"(modal tabungan Rp{dec.franchise.savings_used:,.0f}{loan_desc}, "
                f"laba bersih Rp{dec.franchise.monthly_net_profit:,.0f}/bln."
            ),
            loan=kur_loan,
            initial_dp=dec.franchise.savings_used,
            business_profit_monthly=dec.franchise.monthly_net_profit,
            monthly_invest=0.0,
            meta={
                "franchise_fee": dec.franchise.franchise_fee,
                "savings_used": dec.franchise.savings_used,
                "kur_loan_amount": dec.franchise.kur_loan_amount,
                "monthly_net_profit": dec.franchise.monthly_net_profit,
            },
            **m_style,
        )

        invest_diff = max(0.0, scheduled_pay)
        twin_n = TwinConfig(
            code="N",
            label="Si Investor Pasif & Dividen",
            description=(
                f"Investasi pasif bebas utang bisnis, tabungan utuh dan "
                f"investasikan alokasi modal/cicilan Rp{invest_diff:,.0f}/bln ke {dec.passive_invest.invest_instrument}."
            ),
            initial_dp=0.0,
            monthly_invest=invest_diff,
            instrument=dec.passive_invest.invest_instrument,
            meta={
                "monthly_invest": invest_diff,
                "instrument": dec.passive_invest.invest_instrument,
            },
            **n_style,
        )
        return [twin_m, twin_n]

    if (
        dec.type == "child_education_unitlink_vs_diy"
        and dec.child_education_unitlink
        and dec.child_education_diy
    ):
        o_style = _style("O")
        p_style = _style("P")

        prem = dec.child_education_unitlink.monthly_premium
        term_prem = dec.child_education_diy.term_life_premium_monthly
        diy_invest = max(0.0, prem - term_prem)

        twin_o = TwinConfig(
            code="O",
            label="Si Unit Link Pendidikan",
            description=(
                f"Asuransi Unit Link pendidikan Rp{prem:,.0f}/bln (termasuk biaya asuransi "
                f"dan akuisisi {dec.child_education_unitlink.acquisition_fee_pct_y1*100:.0f}% th-1, "
                f"{dec.child_education_unitlink.acquisition_fee_pct_y2*100:.0f}% th-2)."
            ),
            insurance_monthly=term_prem,
            unitlink_monthly_premium=prem,
            unitlink_acq_y1=dec.child_education_unitlink.acquisition_fee_pct_y1,
            unitlink_acq_y2=dec.child_education_unitlink.acquisition_fee_pct_y2,
            unitlink_acq_y3=dec.child_education_unitlink.acquisition_fee_pct_y3,
            instrument=dec.child_education_unitlink.invest_instrument,
            meta={
                "monthly_premium": prem,
                "acquisition_fee_pct_y1": dec.child_education_unitlink.acquisition_fee_pct_y1,
                "instrument": dec.child_education_unitlink.invest_instrument,
            },
            **o_style,
        )

        twin_p = TwinConfig(
            code="P",
            label="Si Portofolio Mandiri & Asuransi Murni",
            description=(
                f"Pisahkan asuransi jiwa murni Rp{term_prem:,.0f}/bln dan investasikan "
                f"penuh Rp{diy_invest:,.0f}/bln ke {dec.child_education_diy.invest_instrument} (0% biaya akuisisi)."
            ),
            insurance_monthly=term_prem,
            monthly_invest=diy_invest,
            instrument=dec.child_education_diy.invest_instrument,
            meta={
                "term_life_premium": term_prem,
                "monthly_invest": diy_invest,
                "instrument": dec.child_education_diy.invest_instrument,
            },
            **p_style,
        )
        return [twin_o, twin_p]

    return []


def build_twins(
    profile: Profile,
    income_profile: IncomeProfile,
    decisions: list[Decision],
    ruleset: dict,
    growth_annual: float,
    common: dict,
) -> list[TwinConfig]:
    """Baseline + sampai 4 twin (maks 2 keputusan)."""
    twins = [baseline_twin(profile, income_profile, ruleset)]
    seen: set[str] = set()
    for dec in decisions[:2]:
        for t in twins_for_decision(dec, profile, income_profile, ruleset, growth_annual, common):
            if t.code not in seen:
                twins.append(t)
                seen.add(t.code)
    return twins[:5]  # twin 0 + maks 4


def decision_templates() -> list[dict]:
    """Metadata template untuk GET /templates."""
    return [
        {
            "type": "loan_vs_save",
            "title": "Pinjol/Paylater vs Nabung Dulu",
            "twin_a": {"code": "A", "label": "Si Cicilan", **_style("A")},
            "twin_b": {"code": "B", "label": "Si Penabung", **_style("B")},
            "fields": [
                {"key": "loan.amount", "label": "Nominal pinjaman", "type": "currency"},
                {"key": "loan.tenor_months", "label": "Tenor (bulan)", "type": "int", "min": 1, "max": 60},
                {"key": "loan.rate_daily", "label": "Bunga/hari", "type": "percent_daily"},
                {"key": "save.monthly", "label": "Tabungan/bulan", "type": "currency"},
                {"key": "save.instrument", "label": "Instrumen", "type": "instrument"},
            ],
        },
        {
            "type": "study_vs_work",
            "title": "S2 vs Kerja + Upskilling",
            "twin_a": {"code": "C", "label": "Si Akademisi", **_style("C")},
            "twin_b": {"code": "D", "label": "Si Praktisi", **_style("D")},
            "fields": [
                {"key": "study.years", "label": "Durasi (tahun)", "type": "int", "min": 1, "max": 6},
                {"key": "study.total_cost", "label": "Biaya total", "type": "currency"},
                {"key": "study.part_time_work", "label": "Kuliah sambil kerja", "type": "bool"},
                {
                    "key": "study.salary_premium",
                    "label": "Premi gaji S2",
                    "type": "percent",
                    "min": 0.08,
                    "max": 0.25,
                },
                {"key": "work.upskill_monthly", "label": "Biaya kursus/bulan", "type": "currency"},
                {"key": "work.skill_premium", "label": "Premi keahlian", "type": "percent"},
                {"key": "work.premium_after_months", "label": "Premi berlaku setelah (bulan)", "type": "int"},
            ],
        },
        {
            "type": "emergency_vs_invest",
            "title": "Dana Darurat Dulu vs Langsung Investasi",
            "twin_a": {"code": "E", "label": "Si Siaga", **_style("E")},
            "twin_b": {"code": "F", "label": "Si Agresif", **_style("F")},
            "fields": [
                {
                    "key": "emergency.target_months",
                    "label": "Target dana darurat (bulan)",
                    "type": "int",
                    "min": 3,
                    "max": 6,
                },
                {"key": "emergency.invest_monthly", "label": "Investasi/bulan", "type": "currency"},
            ],
        },
        {
            "type": "kpr_vs_rent",
            "title": "Beli Rumah KPR vs Sewa & Investasi",
            "twin_a": {"code": "G", "label": "Si Pemilik Rumah", **_style("G")},
            "twin_b": {"code": "H", "label": "Si Pengontrak & Investor", **_style("H")},
            "fields": [
                {"key": "kpr.property_price", "label": "Harga properti", "type": "currency"},
                {
                    "key": "kpr.down_payment_pct",
                    "label": "Uang muka (DP)",
                    "type": "percent",
                    "min": 0.05,
                    "max": 0.50,
                },
                {
                    "key": "kpr.interest_rate_annual",
                    "label": "Suku bunga KPR/tahun",
                    "type": "percent",
                    "min": 0.03,
                    "max": 0.15,
                },
                {"key": "kpr.tenor_years", "label": "Tenor KPR (tahun)", "type": "int", "min": 5, "max": 30},
                {"key": "rent.rent_monthly", "label": "Biaya sewa/bulan", "type": "currency"},
                {
                    "key": "rent.invest_instrument",
                    "label": "Instrumen investasi selisih",
                    "type": "instrument",
                },
            ],
        },
        {
            "type": "vehicle_lease_vs_cash",
            "title": "Kredit Kendaraan (Leasing OJK) vs Bekas Tunai",
            "twin_a": {"code": "I", "label": "Si Pengkredit Leasing", **_style("I")},
            "twin_b": {"code": "J", "label": "Si Pembeli Bekas & Investor", **_style("J")},
            "fields": [
                {"key": "vehicle_lease.vehicle_price", "label": "Harga kendaraan baru", "type": "currency"},
                {
                    "key": "vehicle_lease.down_payment_pct",
                    "label": "Uang muka (DP)",
                    "type": "percent",
                    "min": 0.10,
                    "max": 0.50,
                },
                {
                    "key": "vehicle_lease.interest_rate_annual",
                    "label": "Bunga leasing/tahun",
                    "type": "percent",
                    "min": 0.05,
                    "max": 0.25,
                },
                {
                    "key": "vehicle_lease.tenor_months",
                    "label": "Tenor leasing (bulan)",
                    "type": "int",
                    "min": 12,
                    "max": 60,
                },
                {"key": "vehicle_cash.used_vehicle_price", "label": "Harga beli bekas tunai", "type": "currency"},
                {
                    "key": "vehicle_cash.invest_instrument",
                    "label": "Instrumen investasi selisih cicilan",
                    "type": "instrument",
                },
            ],
        },
        {
            "type": "wedding_grand_vs_intimate",
            "title": "Pesta Pernikahan Mewah (KTA) vs Nikah Intim & Modal Keluarga",
            "twin_a": {"code": "K", "label": "Si Pesta Akbar", **_style("K")},
            "twin_b": {"code": "L", "label": "Si Intim & Modal Keluarga", **_style("L")},
            "fields": [
                {
                    "key": "wedding_grand.reception_cost",
                    "label": "Estimasi total biaya pesta megah",
                    "type": "currency",
                },
                {
                    "key": "wedding_grand.savings_used",
                    "label": "Porsi dari tabungan sendiri",
                    "type": "currency",
                },
                {
                    "key": "wedding_grand.loan_amount",
                    "label": "Porsi pinjaman KTA/keluarga",
                    "type": "currency",
                },
                {
                    "key": "wedding_grand.tenor_months",
                    "label": "Tenor cicilan KTA (bulan)",
                    "type": "int",
                    "min": 6,
                    "max": 60,
                },
                {
                    "key": "wedding_grand.interest_rate_annual",
                    "label": "Bunga pinjaman/tahun",
                    "type": "percent",
                    "min": 0.05,
                    "max": 0.30,
                },
                {
                    "key": "wedding_intimate.intimate_cost",
                    "label": "Biaya nikah intim/KUA",
                    "type": "currency",
                },
                {
                    "key": "wedding_intimate.invest_instrument",
                    "label": "Instrumen investasi selisih dana",
                    "type": "instrument",
                },
            ],
        },
        {
            "type": "franchise_vs_passive_invest",
            "title": "Franchise Mikro (KUR) vs Portofolio Dividen Pasif",
            "twin_a": {"code": "M", "label": "Si Pebisnis Waralaba", **_style("M")},
            "twin_b": {"code": "N", "label": "Si Investor Pasif & Dividen", **_style("N")},
            "fields": [
                {
                    "key": "franchise.franchise_fee",
                    "label": "Estimasi modal awal franchise",
                    "type": "currency",
                },
                {
                    "key": "franchise.savings_used",
                    "label": "Porsi dari tabungan sendiri",
                    "type": "currency",
                },
                {
                    "key": "franchise.kur_loan_amount",
                    "label": "Porsi pinjaman KUR bank (6%/th)",
                    "type": "currency",
                },
                {
                    "key": "franchise.kur_tenor_months",
                    "label": "Tenor pinjaman KUR (bulan)",
                    "type": "int",
                    "min": 12,
                    "max": 60,
                },
                {
                    "key": "franchise.monthly_net_profit",
                    "label": "Estimasi laba bersih bisnis/bulan",
                    "type": "currency",
                },
                {
                    "key": "passive_invest.invest_instrument",
                    "label": "Instrumen investasi pasif pembanding",
                    "type": "instrument",
                },
            ],
        },
        {
            "type": "child_education_unitlink_vs_diy",
            "title": "Dana Pendidikan Anak: Unit Link vs Tabungan Mandiri + Asuransi Murni",
            "twin_a": {"code": "O", "label": "Si Unit Link Pendidikan", **_style("O")},
            "twin_b": {"code": "P", "label": "Si Portofolio Mandiri & Asuransi Murni", **_style("P")},
            "fields": [
                {
                    "key": "child_education_unitlink.monthly_premium",
                    "label": "Premi bulanan Unit Link (PAYDI)",
                    "type": "currency",
                },
                {
                    "key": "child_education_unitlink.acquisition_fee_pct_y1",
                    "label": "Biaya akuisisi Th-1",
                    "type": "percent",
                    "min": 0.10,
                    "max": 0.90,
                },
                {
                    "key": "child_education_unitlink.invest_instrument",
                    "label": "Subdana investasi polis",
                    "type": "instrument",
                },
                {
                    "key": "child_education_diy.term_life_premium_monthly",
                    "label": "Premi asuransi jiwa murni/bulan",
                    "type": "currency",
                },
                {
                    "key": "child_education_diy.invest_instrument",
                    "label": "Instrumen investasi mandiri",
                    "type": "instrument",
                },
            ],
        },
    ]
