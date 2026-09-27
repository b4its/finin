"""Jalur penghasilan per twin: gaji tetap, uang saku, tidak tetap, S2, upskilling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IncomeProfile:
    income_type: str  # "salary" | "allowance" | "variable"
    income_monthly: float
    income_min: float | None = None
    income_max: float | None = None

    @property
    def base(self) -> float:
        if self.income_type == "variable":
            # Untuk stress test pakai nilai minimum; untuk proyeksi pakai rata-rata.
            if self.income_min is not None and self.income_max is not None:
                return (self.income_min + self.income_max) / 2.0
            return self.income_min if self.income_min is not None else self.income_monthly
        return self.income_monthly

    @property
    def base_min(self) -> float:
        if self.income_type == "variable" and self.income_min is not None:
            return self.income_min
        return self.base


def income_path(
    profile: IncomeProfile,
    growth_annual: float,
    month: int,
    *,
    study: bool = False,
    part_time_monthly: float = 0.0,
    job_wait_months: int = 0,
    graduate_month: int | None = None,
    post_graduate_multiplier: float = 1.0,
    skill_month: int | None = None,
    skill_multiplier: float = 1.0,
    use_min: bool = False,
) -> float:
    """Penghasilan bulan ke-`month` (mulai 0) untuk satu jalur.

    Aturan S2 (Twin Si Akademisi):
      - selama studi: 0 (atau part-time)
      - setelah lulus: masa tunggu kerja, lalu penghasilan * premi S2.
    Aturan upskilling (Twin Si Praktisi):
      - sebelum `skill_month`: penghasilan dasar
      - setelah: penghasilan * premi keahlian.
    """
    base = profile.base_min if use_min else profile.base

    if study:
        if graduate_month is not None and month < graduate_month:
            return part_time_monthly
        # masa tunggu kerja
        wait_end = (graduate_month or 0) + job_wait_months
        if month < wait_end:
            return part_time_monthly
        # setelah kerja: gaji dasar naik bertumbuh, dikali premi S2
        elapsed = month - wait_end
        grown = base * (1.0 + growth_annual) ** (elapsed / 12.0)
        return grown * post_graduate_multiplier

    # jalur kerja / baseline
    grown = base * (1.0 + growth_annual) ** (month / 12.0)
    if skill_month is not None and month >= skill_month:
        grown *= skill_multiplier
    return grown
