"""Perhitungan pinjaman: anuitas, pinjol flat harian, denda, lock cap, macet."""

from __future__ import annotations

from dataclasses import dataclass

from app.engine.regulatory import DAYS_PER_MONTH, lock_cap_amount, total_fee


def annuity_payment(principal: float, annual_rate: float, months: int) -> float:
    """Cicilan anuitas: P = L·i / (1 - (1+i)^-n)."""
    if months <= 0 or principal <= 0:
        return 0.0
    i = annual_rate / 12.0
    if abs(i) < 1e-12:
        return principal / months
    return principal * i / (1 - (1 + i) ** (-months))


def flat_monthly_payment(
    principal: float, rate_daily: float, tenor_months: float, ruleset: dict | None = None
) -> float:
    """Cicilan flat untuk pinjol/paylater (bunga harian), dengan lock cap."""
    if tenor_months <= 0:
        return principal
    return (principal + total_fee(principal, rate_daily, tenor_months, ruleset)) / tenor_months


@dataclass
class Loan:
    """Definisi pinjaman tunggal."""

    kind: str  # "pinjol" | "paylater" | "annuity"
    principal: float
    tenor_months: int
    rate_daily: float = 0.0
    annual_rate: float = 0.0
    penalty_daily: float | None = None
    ruleset: dict | None = None

    @property
    def scheduled_payment(self) -> float:
        if self.kind in ("pinjol", "paylater"):
            return flat_monthly_payment(self.principal, self.rate_daily, self.tenor_months, self.ruleset)
        return annuity_payment(self.principal, self.annual_rate, self.tenor_months)

    @property
    def max_fee(self) -> float:
        return lock_cap_amount(self.principal, self.ruleset)


@dataclass
class LoanState:
    """Status pinjaman berjalan selama simulasi."""

    loan: Loan
    balance: float = 0.0
    months_paid: int = 0
    fee_accrued: float = 0.0
    penalty_accrued: float = 0.0
    arrears_days: float = 0.0
    missed_months: int = 0
    max_arrears_days: float = 0.0

    def __post_init__(self) -> None:
        if self.balance == 0.0:
            self.balance = self.loan.principal

    @property
    def closed(self) -> bool:
        return self.balance <= 1e-6

    @property
    def defaulted(self) -> bool:
        cap = (self.loan.ruleset or {}).get("default_days", 90)
        return self.arrears_days > cap


def accrue_month(state: LoanState) -> float:
    """Bunga/manfaat + denda satu bulan untuk pinjaman yang belum lunas.

    Mengembalikan total beban (fee + penalty) bulan ini. Lock cap diterapkan
    pada akumulasi bunga + denda terhadap pokok awal.
    """
    loan = state.loan
    if state.closed:
        return 0.0

    if loan.kind in ("pinjol", "paylater"):
        daily = loan.rate_daily
    else:
        # anuitas: bunga dari saldo, konversi tahunan -> harian efektif
        daily = (1 + loan.annual_rate) ** (1.0 / 365.0) - 1.0

    fee = state.balance * daily * DAYS_PER_MONTH

    penalty = 0.0
    if state.arrears_days > 0:
        pen_rate = loan.penalty_daily if loan.penalty_daily is not None else daily
        penalty = state.balance * pen_rate * DAYS_PER_MONTH

    # Lock cap: total bunga + denda akumulatif <= 100% pokok.
    room = max(0.0, loan.max_fee - state.fee_accrued - state.penalty_accrued)
    total = fee + penalty
    if total > room:
        if fee >= room:
            penalty = 0.0
            fee = room
        else:
            penalty = room - fee
    state.fee_accrued += fee
    state.penalty_accrued += penalty
    return fee + penalty


def apply_month(
    state: LoanState,
    income_available: float,
    cash_available: float,
) -> tuple[float, float, float]:
    """Proses satu bulan pinjaman.

    Returns:
        (paid, cash_used, amount_due)
    """
    loan = state.loan
    if state.closed:
        return 0.0, 0.0, 0.0

    due = loan.scheduled_payment
    if state.months_paid >= loan.tenor_months:
        due = state.balance  # sisa pelunasan (mis. karena tunggakan)

    accrue_month(state)

    # Sumber pembayaran: sisa penghasilan bulan ini + kas.
    capacity = max(0.0, income_available) + max(0.0, cash_available)
    paid = min(due, state.balance + state.fee_accrued + state.penalty_accrued, capacity)
    if paid < 0:
        paid = 0.0

    cash_used = max(0.0, paid - max(0.0, income_available))

    # Alokasi: pokok dulu (mengurangi saldo), lalu fee/penalty terakumulasi.
    state.balance = max(0.0, state.balance - paid)
    state.months_paid += 1

    if paid + 1e-6 < due:
        # Kurang bayar -> tunggakan bertambah (hari).
        state.arrears_days += DAYS_PER_MONTH
        state.missed_months += 1
    else:
        state.arrears_days = 0.0
    state.max_arrears_days = max(state.max_arrears_days, state.arrears_days)

    if state.balance <= 1e-6:
        state.balance = 0.0
        state.arrears_days = 0.0
    return paid, cash_used, due
