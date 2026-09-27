"""Engine Perpajakan & Jaminan Sosial Indonesia: PPh 21 TER (PP 58/2023) & BPJS.

Regulasi:
  - PP No. 58 Tahun 2023 & PMK No. 168 Tahun 2023 (Tarif Efektif Rata-Rata / TER PPh 21).
  - UU No. 24 Tahun 2011 & PP No. 46 Tahun 2015 (BPJS Ketenagakerjaan: JHT & JP).
  - Perpres No. 64 Tahun 2020 (BPJS Kesehatan).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TERCategory = Literal["A", "B", "C"]

# Plafon upah maksimal jaminan pensiun & kesehatan (standar regulasi 2025/2026)
BPJS_TK_JP_MAX_WAGE = 10_042_300.0
BPJS_KES_MAX_WAGE = 12_000_000.0

# Tabel TER Kategori A (PTKP: TK/0, TK/1, K/0) — PP 58/2023
TER_A_TABLE: list[tuple[float, float]] = [
    (5_400_000, 0.000),
    (5_650_000, 0.0025),
    (5_950_000, 0.005),
    (6_300_000, 0.0075),
    (6_750_000, 0.010),
    (7_500_000, 0.0125),
    (8_550_000, 0.015),
    (9_650_000, 0.0175),
    (10_050_000, 0.020),
    (10_350_000, 0.0225),
    (10_700_000, 0.025),
    (11_050_000, 0.030),
    (11_600_000, 0.035),
    (12_500_000, 0.040),
    (13_750_000, 0.050),
    (15_100_000, 0.060),
    (16_950_000, 0.070),
    (19_750_000, 0.080),
    (24_150_000, 0.090),
    (26_450_000, 0.100),
    (28_000_000, 0.110),
    (30_050_000, 0.120),
    (32_400_000, 0.130),
    (35_400_000, 0.140),
    (39_100_000, 0.150),
    (43_850_000, 0.160),
    (47_800_000, 0.170),
    (51_400_000, 0.180),
    (56_300_000, 0.190),
    (62_200_000, 0.200),
    (68_600_000, 0.210),
    (77_500_000, 0.220),
    (89_000_000, 0.230),
    (101_900_000, 0.240),
    (114_000_000, 0.250),
    (126_800_000, 0.260),
    (144_100_000, 0.270),
    (178_300_000, 0.280),
    (231_500_000, 0.290),
    (304_900_000, 0.300),
    (425_400_000, 0.310),
    (558_800_000, 0.320),
    (1_411_000_000, 0.330),
    (float("inf"), 0.340),
]

# Tabel TER Kategori B (PTKP: TK/2, TK/3, K/1, K/2) — PP 58/2023
TER_B_TABLE: list[tuple[float, float]] = [
    (6_200_000, 0.000),
    (6_500_000, 0.0025),
    (6_850_000, 0.005),
    (7_300_000, 0.0075),
    (9_200_000, 0.010),
    (10_750_000, 0.015),
    (11_250_000, 0.020),
    (11_600_000, 0.025),
    (12_600_000, 0.030),
    (13_600_000, 0.040),
    (14_950_000, 0.050),
    (16_400_000, 0.060),
    (18_450_000, 0.070),
    (21_850_000, 0.080),
    (26_000_000, 0.090),
    (27_700_000, 0.100),
    (29_350_000, 0.110),
    (31_450_000, 0.120),
    (33_950_000, 0.130),
    (37_100_000, 0.140),
    (41_100_000, 0.150),
    (45_800_000, 0.160),
    (49_500_000, 0.170),
    (53_800_000, 0.180),
    (58_500_000, 0.190),
    (64_000_000, 0.200),
    (71_000_000, 0.210),
    (80_000_000, 0.220),
    (93_000_000, 0.230),
    (109_000_000, 0.240),
    (129_000_000, 0.250),
    (163_000_000, 0.260),
    (211_000_000, 0.270),
    (274_000_000, 0.280),
    (345_000_000, 0.290),
    (461_000_000, 0.300),
    (596_000_000, 0.310),
    (754_000_000, 0.320),
    (1_405_000_000, 0.330),
    (float("inf"), 0.340),
]

# Tabel TER Kategori C (PTKP: K/3) — PP 58/2023
TER_C_TABLE: list[tuple[float, float]] = [
    (6_600_000, 0.000),
    (6_950_000, 0.0025),
    (7_350_000, 0.005),
    (7_800_000, 0.0075),
    (8_850_000, 0.010),
    (9_800_000, 0.0125),
    (10_950_000, 0.015),
    (11_200_000, 0.0175),
    (12_050_000, 0.020),
    (12_950_000, 0.030),
    (14_150_000, 0.040),
    (15_550_000, 0.050),
    (17_050_000, 0.060),
    (19_500_000, 0.070),
    (22_700_000, 0.080),
    (26_600_000, 0.090),
    (28_100_000, 0.100),
    (30_100_000, 0.110),
    (32_600_000, 0.120),
    (35_400_000, 0.130),
    (38_900_000, 0.140),
    (43_400_000, 0.150),
    (47_600_000, 0.160),
    (51_500_000, 0.170),
    (56_000_000, 0.180),
    (61_000_000, 0.190),
    (67_000_000, 0.200),
    (74_500_000, 0.210),
    (84_000_000, 0.220),
    (97_000_000, 0.230),
    (113_000_000, 0.240),
    (135_000_000, 0.250),
    (172_000_000, 0.260),
    (224_000_000, 0.270),
    (290_000_000, 0.280),
    (365_000_000, 0.290),
    (486_000_000, 0.300),
    (628_000_000, 0.310),
    (792_000_000, 0.320),
    (1_419_000_000, 0.330),
    (float("inf"), 0.340),
]


def ter_rate_for(gross_monthly: float, category: TERCategory = "A") -> float:
    """Cari tarif efektif TER bulanan sesuai tabel PP 58/2023."""
    table = TER_A_TABLE
    if category == "B":
        table = TER_B_TABLE
    elif category == "C":
        table = TER_C_TABLE

    for limit, rate in table:
        if gross_monthly <= limit:
            return rate
    return 0.340


@dataclass(frozen=True)
class StatutoryDeductionResult:
    gross_monthly: float
    ter_category: str
    pph21_monthly: float
    pph21_effective_rate: float
    # Potongan pekerja (mengurangi slip gaji)
    bpjs_jht_worker: float
    bpjs_jp_worker: float
    bpjs_kes_worker: float
    total_worker_deductions: float
    net_take_home_pay: float
    # Kontribusi pemberi kerja (masuk ke dana pensiun & jaminan)
    bpjs_jht_employer: float
    bpjs_jp_employer: float
    bpjs_kes_employer: float
    total_jht_monthly_savings: float  # Pekerja (2%) + Employer (3.7%) = 5.7%

    def to_dict(self) -> dict:
        return {
            "gross_monthly": self.gross_monthly,
            "ter_category": self.ter_category,
            "pph21_monthly": self.pph21_monthly,
            "pph21_effective_rate": self.pph21_effective_rate,
            "bpjs_jht_worker": self.bpjs_jht_worker,
            "bpjs_jp_worker": self.bpjs_jp_worker,
            "bpjs_kes_worker": self.bpjs_kes_worker,
            "total_worker_deductions": self.total_worker_deductions,
            "net_take_home_pay": self.net_take_home_pay,
            "bpjs_jht_employer": self.bpjs_jht_employer,
            "bpjs_jp_employer": self.bpjs_jp_employer,
            "bpjs_kes_employer": self.bpjs_kes_employer,
            "total_jht_monthly_savings": self.total_jht_monthly_savings,
        }


def calculate_statutory_deductions(
    gross_monthly: float,
    ter_category: TERCategory = "A",
    *,
    include_bpjs: bool = True,
) -> StatutoryDeductionResult:
    """Hitung lengkap slip gaji bersih resmi: PPh 21 TER, BPJS Ketenagakerjaan & Kesehatan."""
    if gross_monthly <= 0:
        return StatutoryDeductionResult(
            gross_monthly=0.0,
            ter_category=ter_category,
            pph21_monthly=0.0,
            pph21_effective_rate=0.0,
            bpjs_jht_worker=0.0,
            bpjs_jp_worker=0.0,
            bpjs_kes_worker=0.0,
            total_worker_deductions=0.0,
            net_take_home_pay=0.0,
            bpjs_jht_employer=0.0,
            bpjs_jp_employer=0.0,
            bpjs_kes_employer=0.0,
            total_jht_monthly_savings=0.0,
        )

    rate_ter = ter_rate_for(gross_monthly, ter_category)
    pph21 = round(gross_monthly * rate_ter)

    if include_bpjs:
        # Batas upah terdaftar
        jp_base = min(gross_monthly, BPJS_TK_JP_MAX_WAGE)
        kes_base = min(gross_monthly, BPJS_KES_MAX_WAGE)

        # Potongan pekerja
        jht_worker = round(gross_monthly * 0.02)
        jp_worker = round(jp_base * 0.01)
        kes_worker = round(kes_base * 0.01)

        # Kontribusi pemberi kerja
        jht_employer = round(gross_monthly * 0.037)
        jp_employer = round(jp_base * 0.02)
        kes_employer = round(kes_base * 0.04)
    else:
        jht_worker = jp_worker = kes_worker = 0.0
        jht_employer = jp_employer = kes_employer = 0.0

    total_worker = pph21 + jht_worker + jp_worker + kes_worker
    net_thp = max(0.0, gross_monthly - total_worker)
    total_jht = jht_worker + jht_employer

    return StatutoryDeductionResult(
        gross_monthly=gross_monthly,
        ter_category=ter_category,
        pph21_monthly=float(pph21),
        pph21_effective_rate=rate_ter,
        bpjs_jht_worker=float(jht_worker),
        bpjs_jp_worker=float(jp_worker),
        bpjs_kes_worker=float(kes_worker),
        total_worker_deductions=float(total_worker),
        net_take_home_pay=float(net_thp),
        bpjs_jht_employer=float(jht_employer),
        bpjs_jp_employer=float(jp_employer),
        bpjs_kes_employer=float(kes_employer),
        total_jht_monthly_savings=float(total_jht),
    )


def project_jht_wealth(
    monthly_gross: float,
    current_age: int,
    retirement_age: int = 56,
    annual_return: float = 0.056,
    annual_salary_growth: float = 0.05,
) -> dict:
    """Proyeksikan akumulasi dana JHT BPJS Ketenagakerjaan hingga usia pensiun 56 tahun."""
    years = max(1, retirement_age - current_age)
    total_balance = 0.0
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1

    current_gross = monthly_gross
    for y in range(years):
        jht_monthly = current_gross * 0.057  # 2% pekerja + 3.7% pemberi kerja
        for _ in range(12):
            total_balance = (total_balance + jht_monthly) * (1 + monthly_rate)
        current_gross *= 1 + annual_salary_growth

    return {
        "current_age": current_age,
        "retirement_age": retirement_age,
        "years_to_retirement": years,
        "projected_jht_lump_sum": round(total_balance),
        "note": "Akumulasi JHT total 5,7% upah (2% pekerja + 3,7% pemberi kerja) dengan asumsi imbal hasil pengembangan 5,6%/tahun.",
    }
