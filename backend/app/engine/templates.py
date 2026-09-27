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
    # biaya kuliah (dibayar bulanan)
    study_cost: float = 0.0
    # biaya kursus bulanan
    upskill_monthly: float = 0.0
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

    # emergency_vs_invest
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
    ]
