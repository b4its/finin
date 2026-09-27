"""Regulatory Guard — aturan OJK berversi.

Sumber: SEOJK 19/SEOJK.06/2025 (ditetapkan 31 Juli 2025), mencabut SEOJK 19/2023.
Nilai default disimpan di data/assumptions/ID-2026-09.json agar bisa diperbarui
tanpa mengubah kode. Modul ini hanya memuat fallback dan logika pengecekan.

Batas pinjol konsumtif:
  - tenor <= 6 bulan : bunga 0,3%/hari, denda 0,3%/hari
  - tenor  > 6 bulan : bunga 0,2%/hari, denda 0,2%/hari
  - lock cap         : bunga + denda <= 100% pokok
  - DSR              : cicilan <= 30% penghasilan (sejak 2026)
  - macet (TWP90)    : tunggakan > 90 hari
"""

from __future__ import annotations

from dataclasses import dataclass

DAYS_PER_MONTH = 365 / 12  # ≈ 30,42 hari

# Fallback jika set asumsi tidak menyertakan blok regulatory.
RULESET: dict = {
    "version": "SEOJK-19-2025",
    "replaces": "SEOJK-19-2023",
    "effective_from": "2025-07-31",
    "consumer_caps": [
        (6, 0.003, 0.003),
        (None, 0.002, 0.002),
    ],
    "lock_cap_ratio": 1.00,
    "dsr_cap": 0.30,
    "default_days": 90,
}


@dataclass(frozen=True)
class Flag:
    level: str  # "red" | "orange" | "yellow"
    code: str
    msg: str

    def to_dict(self) -> dict:
        return {"level": self.level, "code": self.code, "msg": self.msg}


def ruleset_from_assumptions(regulatory: dict | None) -> dict:
    """Bangun ruleset dari blok regulatory pada set asumsi."""
    if not regulatory:
        return dict(RULESET)
    caps = []
    for cap in regulatory.get("consumer_caps", []):
        caps.append(
            (
                cap.get("tenor_max_months"),
                cap.get("rate_daily_max"),
                cap.get("penalty_daily_max"),
            )
        )
    return {
        "version": regulatory.get("ruleset_version", RULESET["version"]),
        "replaces": regulatory.get("replaces", RULESET["replaces"]),
        "effective_from": regulatory.get("effective_from", RULESET["effective_from"]),
        "consumer_caps": caps or RULESET["consumer_caps"],
        "lock_cap_ratio": regulatory.get("lock_cap_ratio", RULESET["lock_cap_ratio"]),
        "dsr_cap": regulatory.get("dsr_cap", RULESET["dsr_cap"]),
        "default_days": regulatory.get("default_days", RULESET["default_days"]),
    }


def cap_for(tenor_months: float, ruleset: dict | None = None) -> tuple[float, float]:
    """Kembalikan (bunga_harian_max, denda_harian_max) untuk tenor tertentu."""
    rs = ruleset or RULESET
    caps = rs["consumer_caps"]
    # Kapas dari tenor terkecil yang menampung tenor ini.
    for max_t, rate, fee in sorted(caps, key=lambda c: (c[0] is None, c[0] or 0)):
        if max_t is None or tenor_months <= max_t:
            return rate, fee
    # Fallback ke kap terakhir.
    _, rate, fee = caps[-1]
    return rate, fee


def lock_cap_amount(principal: float, ruleset: dict | None = None) -> float:
    rs = ruleset or RULESET
    return principal * rs["lock_cap_ratio"]


def total_fee(principal: float, rate_daily: float, tenor_months: float, ruleset: dict | None = None) -> float:
    """Total manfaat (bunga flat harian) dengan lock cap diterapkan."""
    days = tenor_months * DAYS_PER_MONTH
    raw = principal * rate_daily * days
    return min(raw, lock_cap_amount(principal, ruleset))


def installment_for(
    principal: float, rate_daily: float, tenor_months: float, ruleset: dict | None = None
) -> float:
    """Cicilan flat per bulan untuk pinjol/paylater."""
    if tenor_months <= 0:
        return principal
    return (principal + total_fee(principal, rate_daily, tenor_months, ruleset)) / tenor_months


def check_pinjol(
    amount: float,
    tenor_months: float,
    rate_daily: float,
    income_monthly: float,
    existing_payment: float = 0.0,
    penalty_daily: float | None = None,
    ruleset: dict | None = None,
) -> list[Flag]:
    """Pemeriksaan aturan OJK untuk template pinjol/paylater."""
    rs = ruleset or RULESET
    flags: list[Flag] = []
    rate_cap, penalty_cap = cap_for(tenor_months, rs)

    if rate_daily > rate_cap + 1e-12:
        flags.append(
            Flag(
                "red",
                "ABOVE_OJK_CAP",
                f"Bunga {rate_daily:.2%}/hari di atas batas OJK {rate_cap:.1%}/hari untuk tenor ini — "
                "indikasi pinjol ilegal. Cek status penyedia di situs resmi OJK.",
            )
        )

    effective_penalty = penalty_daily if penalty_daily is not None else rate_daily
    if effective_penalty > penalty_cap + 1e-12:
        flags.append(
            Flag(
                "red",
                "PENALTY_ABOVE_OJK_CAP",
                f"Denda {effective_penalty:.2%}/hari di atas batas OJK {penalty_cap:.1%}/hari untuk tenor ini.",
            )
        )

    installment = installment_for(amount, rate_daily, tenor_months, rs)
    if income_monthly > 0:
        dsr = (installment + existing_payment) / income_monthly
        if dsr > rs["dsr_cap"] + 1e-12:
            flags.append(
                Flag(
                    "orange",
                    "DSR_OVER_30",
                    f"Cicilan {(installment + existing_payment):,.0f}/bulan ≈ {dsr:.0%} penghasilan, "
                    f"melebihi batas kemampuan bayar OJK {rs['dsr_cap']:.0%}.",
                )
            )
    return flags


def check_dsr(installment: float, income_monthly: float, ruleset: dict | None = None) -> Flag | None:
    """Bendera oranye jika rasio cicilan melebihi batas DSR."""
    rs = ruleset or RULESET
    if income_monthly <= 0:
        return None
    dsr = installment / income_monthly
    if dsr > rs["dsr_cap"] + 1e-12:
        return Flag(
            "orange",
            "DSR_OVER_30",
            f"Total cicilan ≈ {dsr:.0%} penghasilan, melebihi batas OJK {rs['dsr_cap']:.0%}.",
        )
    return None


def slik_flag() -> Flag:
    return Flag(
        "yellow",
        "SLIK_DEFAULT",
        "Tercatat di SLIK OJK; akses kredit formal (misalnya KPR) bisa terhambat.",
    )


def regulatory_payload(regulatory: dict | None) -> dict:
    """Representasi JSON untuk endpoint /assumptions."""
    rs = ruleset_from_assumptions(regulatory)
    return {
        "version": rs["version"],
        "replaces": rs["replaces"],
        "effective_from": rs["effective_from"],
        "consumer_caps": [
            {"tenor_max_months": t, "rate_daily_max": r, "penalty_daily_max": f}
            for t, r, f in rs["consumer_caps"]
        ],
        "lock_cap_ratio": rs["lock_cap_ratio"],
        "dsr_cap": rs["dsr_cap"],
        "default_days": rs["default_days"],
    }
