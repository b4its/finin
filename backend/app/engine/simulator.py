"""Loop simulasi bulanan deterministik.

Satu bulan = 365/12 ≈ 30,42 hari (lihat DAYS_PER_MONTH).
Menghitung: bunga majemuk, inflasi, pertumbuhan penghasilan, cicilan,
denda, lock cap, status macet (>90 hari), tanggungan keluarga ikut inflasi,
dana darurat, net worth nominal + riil.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.assumptions import monthly_rate
from app.engine.income import IncomeProfile, income_path
from app.engine.loans import Loan, LoanState, apply_month
from app.engine.regulatory import ruleset_from_assumptions
from app.engine.templates import TwinConfig
from app.schemas.input import Profile


@dataclass
class Shock:
    """Definisi guncangan untuk stress test."""

    code: str
    label: str
    start_month: int
    # penghasilan dikalikan 0? atau biaya tambahan
    income_multiplier: float = 1.0
    duration_months: int = 0
    extra_cost: float = 0.0
    note: str = ""


@dataclass
class MonthSnapshot:
    month: int
    income: float
    living: float
    paid_debt: float
    cash: float
    invest: float
    debt: float
    net_worth: float
    net_worth_real: float
    cashflow: float
    emergency_months: float
    dsr: float
    defaulted: bool
    new_debt: float = 0.0


@dataclass
class SimResult:
    config: TwinConfig
    months: list[MonthSnapshot] = field(default_factory=list)
    max_arrears_days: float = 0.0
    defaulted_months: int = 0
    dsr_over_months: int = 0

    def at_month(self, m: int) -> MonthSnapshot:
        m = max(0, min(m, len(self.months) - 1))
        return self.months[m]

    def at_year(self, y: int) -> MonthSnapshot:
        return self.at_month(y * 12)


def simulate(
    cfg: TwinConfig,
    profile: Profile,
    income_profile: IncomeProfile,
    assumptions: dict,
    ruleset: dict,
    *,
    months: int = 240,
    shock: Shock | None = None,
    use_min_income: bool = False,
) -> SimResult:
    """Jalankan simulasi bulanan untuk satu twin."""
    rs = ruleset or ruleset_from_assumptions(None)
    infl = monthly_rate(assumptions.get("inflation", 0.03))
    rates = assumptions.get("returns", {})
    growth = assumptions.get("salary_growth", 0.05)
    job_wait = int(assumptions.get("job_wait_months", 3))

    r_inv = monthly_rate(rates.get(cfg.instrument, rates.get("money_market", 0.045)))
    r_cash = monthly_rate(rates.get("savings", 0.01))

    cash = profile.savings
    if cfg.initial_dp > 0:
        cash = max(0.0, cash - cfg.initial_dp)
    invest = 0.0

    # utang berjalan pengguna (di semua twin, ceteris paribus)
    loans: list[LoanState] = []
    if profile.existing_debt.principal > 0:
        debt_loan = Loan(
            kind="annuity",
            principal=profile.existing_debt.principal,
            tenor_months=profile.existing_debt.tenor_months or 12,
            annual_rate=profile.existing_debt.annual_rate or 0.0,
            ruleset=rs,
        )
        loans.append(LoanState(loan=debt_loan))

    # pinjaman spesifik twin
    if cfg.loan is not None:
        loans.append(LoanState(loan=cfg.loan))

    base_expense = profile.expense_monthly + profile.dependents_monthly
    emergency_target = base_expense * cfg.emergency_target_months

    result = SimResult(config=cfg)
    new_debt_total = 0.0

    for m in range(months + 1):
        income = income_path(
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
            use_min=use_min_income,
        ) + cfg.business_profit_monthly

        rent_cost = (cfg.rent_monthly * (1 + infl) ** m) if cfg.rent_monthly > 0 else 0.0
        extra_cost = cfg.study_cost + cfg.upskill_monthly + rent_cost + cfg.insurance_monthly
        if shock is not None and shock.start_month <= m < shock.start_month + max(shock.duration_months, 1):
            income *= shock.income_multiplier
            extra_cost += shock.extra_cost

        living = (
            (profile.expense_monthly) * (1 + infl) ** m
            + profile.dependents_monthly * (1 + infl) ** m
            + extra_cost
        )

        # Net penghasilan tersedia untuk cicilan setelah biaya hidup.
        available = income - living

        # Bayar cicilan (semua pinjaman).
        paid_total = 0.0
        cash_used_total = 0.0
        for ls in loans:
            paid, cash_used, _ = apply_month(ls, available - paid_total, cash)
            paid_total += paid
            cash_used_total += cash_used
        cash -= cash_used_total

        # Sisa arus kas.
        surplus = available - paid_total

        # Sisa baki pinjaman bulan ini (untuk snapshot).
        debt_balance = sum(ls.balance for ls in loans if not ls.closed)

        if surplus >= 0:
            # Alokasikan surplus: dana darurat dulu (jika twin Si Siaga) lalu investasi.
            if cfg.emergency_first and cash < emergency_target:
                room = emergency_target - cash
                to_emergency = min(surplus, room)
                cash += to_emergency
                surplus -= to_emergency

            if cfg.unitlink_monthly_premium > 0:
                prem_target = cfg.unitlink_monthly_premium
                prem_investable = max(0.0, prem_target - cfg.insurance_monthly)
                prem = min(surplus, prem_investable)
                # Biaya akuisisi PAYDI (SEOJK No. 5/SEOJK.05/2022)
                yr = m // 12 + 1
                if yr == 1:
                    acq_rate = cfg.unitlink_acq_y1
                elif yr == 2:
                    acq_rate = cfg.unitlink_acq_y2
                elif yr == 3:
                    acq_rate = cfg.unitlink_acq_y3
                else:
                    acq_rate = 0.05
                fee = prem_target * acq_rate
                invest += max(0.0, prem - fee)
                cash += surplus - prem
            else:
                contrib = min(surplus, cfg.monthly_invest)
                invest += contrib
                cash += surplus - contrib
        else:
            # Defisit: pakai kas; kalau kas habis, jual investasi.
            cash += surplus
            if cash < 0:
                invest += cash
                cash = 0.0
                if invest < 0:
                    # Benar-benar kehabisan: catat sebagai utang baru baru (tidak modal).
                    new_debt_total += -invest
                    invest = 0.0

        # Bunga / pertumbuhan.
        invest *= 1 + r_inv
        cash *= 1 + r_cash

        property_val = (
            cfg.property_initial_value * (1 + cfg.property_appreciation_annual / 12) ** m
            if cfg.property_initial_value > 0
            else 0.0
        )

        vehicle_val = (
            cfg.vehicle_initial_value * max(0.05, (1 - cfg.vehicle_depreciation_annual / 12) ** m)
            if cfg.vehicle_initial_value > 0
            else 0.0
        )

        debt_balance = sum(ls.balance for ls in loans if not ls.closed)
        total_invest = max(invest, 0.0) + property_val + vehicle_val
        net_worth = cash + total_invest - debt_balance
        real = net_worth / (1 + assumptions.get("inflation", 0.03)) ** (m / 12.0)

        monthly_debt_payment = sum(ls.loan.scheduled_payment for ls in loans if not ls.closed)
        dsr = (monthly_debt_payment / income) if income > 0 else 0.0
        defaulted = any(ls.defaulted for ls in loans)
        emergency_months = cash / base_expense if base_expense > 0 else 0.0

        snap = MonthSnapshot(
            month=m,
            income=income,
            living=living,
            paid_debt=paid_total,
            cash=max(cash, 0.0),
            invest=total_invest,
            debt=debt_balance,
            net_worth=net_worth,
            net_worth_real=real,
            cashflow=surplus,
            emergency_months=emergency_months,
            dsr=dsr,
            defaulted=defaulted,
            new_debt=0.0,
        )
        result.months.append(snap)
        if defaulted:
            result.defaulted_months += 1
        if dsr > rs.get("dsr_cap", 0.30) and income > 0:
            result.dsr_over_months += 1
        for ls in loans:
            result.max_arrears_days = max(result.max_arrears_days, ls.max_arrears_days)

    result.months[-1].new_debt = new_debt_total
    return result


def yearly_series(result: SimResult, max_year: int = 20) -> list[dict]:
    """Ambil titik tahunan (0..max_year) dari hasil bulanan."""
    out = []
    for y in range(0, max_year + 1):
        s = result.at_year(y)
        out.append(
            {
                "year": y,
                "net_worth": s.net_worth,
                "net_worth_real": s.net_worth_real,
                "debt": s.debt,
                "cash": s.cash,
                "invest": s.invest,
                "cashflow": s.cashflow,
                "emergency_months": s.emergency_months,
                "dsr": s.dsr,
                "defaulted": s.defaulted,
            }
        )
    return out


def compute_milestones(
    result: SimResult,
    base_expense: float = 0.0,
    emergency_target_months: float = 3.0,
) -> dict[str, int | None]:
    """Hitung bulan pencapaian tonggak finansial penting (0..horizon) atau None jika belum tercapai."""
    target_ef = max(base_expense * emergency_target_months, 1.0)
    fire_target = max(base_expense * 12 * 25, 1.0)
    has_debt = any(m.debt > 0 for m in result.months)

    ef_month: int | None = None
    nw100_month: int | None = None
    debt_free_month: int | None = None
    nw1b_month: int | None = None
    fire_month: int | None = None

    for m in result.months:
        if ef_month is None and (
            m.emergency_months >= emergency_target_months or (base_expense > 0 and m.cash >= target_ef)
        ):
            ef_month = m.month
        if nw100_month is None and m.net_worth >= 100_000_000:
            nw100_month = m.month
        if nw1b_month is None and m.net_worth >= 1_000_000_000:
            nw1b_month = m.month
        if fire_month is None and base_expense > 0 and m.net_worth_real >= fire_target:
            fire_month = m.month
        if has_debt and debt_free_month is None and m.month >= 1 and m.debt <= 0.01:
            debt_free_month = m.month

    if not has_debt:
        debt_free_month = 0

    return {
        "emergency_fund_full": ef_month,
        "net_worth_100m": nw100_month,
        "debt_free": debt_free_month,
        "net_worth_1b": nw1b_month,
        "financial_independence": fire_month,
    }


def summary(result: SimResult, base_expense: float = 0.0) -> dict:
    """Metrik pada tahun 5/10/20 serta tonggak capaian finansial."""
    out: dict = {}
    for y in (5, 10, 20):
        s = result.at_year(y)
        out[f"year_{y}"] = {
            "year": y,
            "net_worth": s.net_worth,
            "net_worth_real": s.net_worth_real,
            "debt": s.debt,
            "emergency_months": s.emergency_months,
            "avg_dsr": s.dsr,
            "defaulted": s.defaulted,
        }
    # rata-rata DSR dan dana darurat minimum sepanjang horizon
    seen = result.months[1:] or result.months
    out["avg_dsr"] = sum(m.dsr for m in seen) / len(seen)
    out["min_emergency_months"] = min(m.emergency_months for m in seen)
    out["max_net_worth_real"] = max(m.net_worth_real for m in seen)
    out["defaulted_months"] = result.defaulted_months
    out["dsr_over_months"] = result.dsr_over_months
    out["final_net_worth"] = seen[-1].net_worth
    out["final_net_worth_real"] = seen[-1].net_worth_real
    out["milestones"] = compute_milestones(
        result,
        base_expense=base_expense,
        emergency_target_months=float(result.config.emergency_target_months),
    )
    return out

