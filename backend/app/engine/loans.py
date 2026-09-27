"""Perhitungan pinjaman: anuitas, pinjol flat harian, denda, lock cap, macet.

Dua model bunga:
  - **Anuitas** (KPR, kredit motor, dsb.): bunga dikenakan atas *saldo* berjalan
    lalu ditambahkan ke saldo; cicilan tetap P = L·i / (1 − (1+i)^-n) melunasi
    pokok + bunga selama tenor. Total bunga bergantung pada kecepatan pelunasan.
  - **Pinjol/paylater flat harian**: total manfaat dihitung di depan
    (pokok × rate_harian × hari), dibatasi *lock cap* 100% pokok, lalu dibagi
    rata sepanjang tenor. Bunga tidak menambah saldo pokok.
"""

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
    def is_flat(self) -> bool:
        return self.kind in ("pinjol", "paylater")

    @property
    def scheduled_payment(self) -> float:
        if self.is_flat:
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
    fee_accrued: float = 0.0  # bunga/manfaat yang sudah diakui (flat atau anuitas)
    penalty_accrued: float = 0.0
    principal_paid: float = 0.0
    interest_paid: float = 0.0
    arrears_days: float = 0.0
    missed_months: int = 0
    max_arrears_days: float = 0.0

    def __post_init__(self) -> None:
        if self.balance == 0.0:
            self.balance = self.loan.principal

    @property
    def closed(self) -> bool:
        if self.balance > 1e-6:
            return False
        if self.loan.is_flat:
            # Flat: lunas bila pokok + bunga + denda sudah terbayar.
            return (self.fee_accrued - self.interest_paid) <= 1e-6 and self.penalty_accrued <= 1e-6
        return True

    @property
    def defaulted(self) -> bool:
        cap = (self.loan.ruleset or {}).get("default_days", 90)
        return self.arrears_days > cap


def _daily_rate(loan: Loan) -> float:
    if loan.is_flat:
        return loan.rate_daily
    return (1.0 + loan.annual_rate) ** (1.0 / 365.0) - 1.0


def accrue_month(state: LoanState) -> float:
    """Akru bunga/manfaat + denda satu bulan.

    - Anuitas: bunga ditambahkan ke `balance` (kapitalisasi) sehingga dilunasi
      lewat cicilan; total bunga bergantung pada saldo berjalan.
    - Flat (pinjol/paylater): total manfaat dihitung di depan (flat) dan diakui
      sekali pada bulan pertama, lalu dibayar sepanjang tenor lewat cicilan tetap;
      bunga *tidak* menambah pokok. Lock cap 100% pokok berlaku untuk total
      bunga + denda akumulatif pada kedua model.
    """
    loan = state.loan
    if state.closed:
        return 0.0

    if loan.is_flat:
        # Manfaat flat diakui sekali di awal (bulan ke-0). Denda boleh berjalan
        # atas saldo bila menunggak.
        if state.fee_accrued <= 1e-9:
            interest = min(total_fee(loan.principal, loan.rate_daily, loan.tenor_months, loan.ruleset), loan.max_fee)
        else:
            interest = 0.0
        penalty = 0.0
        if state.arrears_days > 0:
            pen_rate = loan.penalty_daily if loan.penalty_daily is not None else loan.rate_daily
            penalty = state.balance * pen_rate * DAYS_PER_MONTH
        room = max(0.0, loan.max_fee - state.fee_accrued - state.penalty_accrued)
        total = interest + penalty
        if total > room:
            if interest >= room:
                penalty = 0.0
                interest = room
            else:
                penalty = room - interest
        state.fee_accrued += interest
        state.penalty_accrued += penalty
        return interest + penalty

    # Anuitas
    daily = _daily_rate(loan)
    interest = state.balance * daily * DAYS_PER_MONTH

    penalty = 0.0
    if state.arrears_days > 0:
        pen_rate = loan.penalty_daily if loan.penalty_daily is not None else daily
        penalty = state.balance * pen_rate * DAYS_PER_MONTH

    room = max(0.0, loan.max_fee - state.fee_accrued - state.penalty_accrued)
    total = interest + penalty
    if total > room:
        if interest >= room:
            penalty = 0.0
            interest = room
        else:
            penalty = room - interest

    state.fee_accrued += interest
    state.penalty_accrued += penalty
    # Anuitas: kapitalisasi bunga + denda ke saldo agar dilunasi via cicilan.
    state.balance += interest + penalty
    return interest + penalty


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

    accrue_month(state)

    if loan.is_flat:
        # Sisa kewajiban flat = sisa pokok + sisa bunga + denda yang belum dibayar.
        outstanding_interest = max(0.0, state.fee_accrued - state.interest_paid)
        outstanding_penalty = max(0.0, state.penalty_accrued)
        due = loan.scheduled_payment
        remaining = state.balance + outstanding_interest + outstanding_penalty
        if state.months_paid >= loan.tenor_months:
            due = remaining
        capacity = max(0.0, income_available) + max(0.0, cash_available)
        paid = max(0.0, min(due, remaining, capacity))

        # Alokasi: bunga & denda dulu, lalu pokok (kurangi saldo).
        pay_interest = min(paid, outstanding_interest)
        state.interest_paid += pay_interest
        rest = paid - pay_interest
        pay_penalty = min(rest, outstanding_penalty)
        state.penalty_accrued = max(0.0, state.penalty_accrued - pay_penalty)
        rest -= pay_penalty
        pay_principal = min(rest, state.balance)
        state.balance = max(0.0, state.balance - pay_principal)
        state.principal_paid += pay_principal
    else:
        # Anuitas: cicilan tetap P; sebagian bunga, sebagian pokok.
        due = loan.scheduled_payment
        if state.months_paid >= loan.tenor_months:
            due = state.balance
        capacity = max(0.0, income_available) + max(0.0, cash_available)
        paid = max(0.0, min(due, state.balance, capacity))
        # Saldo sudah termasuk bunga terkapitalisasi dari accrue_month.
        state.balance = max(0.0, state.balance - paid)
        state.principal_paid += paid
        state.interest_paid += paid  # untuk anuitas, "paid" melunasi saldo berjalan

    cash_used = max(0.0, paid - max(0.0, income_available))
    state.months_paid += 1

    if paid + 1e-6 < due:
        state.arrears_days += DAYS_PER_MONTH
        state.missed_months += 1
    else:
        state.arrears_days = 0.0
    state.max_arrears_days = max(state.max_arrears_days, state.arrears_days)

    if state.balance <= 1e-6:
        state.balance = 0.0
        if loan.is_flat and state.fee_accrued - state.interest_paid <= 1e-6:
            state.arrears_days = 0.0
    return paid, cash_used, due
