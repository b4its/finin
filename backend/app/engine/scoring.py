"""Skor rekomendasi deterministik (PRD §8).

`0,30·NW_riil_th10(norm) + 0,25·min(dana_darurat_min/6, 1)
 + 0,20·(1 − min(DSR_rata/0,30, 1)) + 0,15·lolos_stress + 0,10·menang_di_preset/3`

Aturan keras: twin yang macet ATAU punya DSR > 30% selama lebih dari 6 bulan
tidak boleh direkomendasikan, kecuali semua twin mengalaminya.
"""

from __future__ import annotations

from app.engine.simulator import SimResult, summary
from app.engine.templates import TwinConfig

WEIGHTS = {
    "net_worth_real": 0.30,
    "emergency": 0.25,
    "dsr": 0.20,
    "stress": 0.15,
    "robust": 0.10,
}


def _norm(value: float, lo: float, hi: float) -> float:
    if hi - lo < 1e-9:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def score_breakdown(
    result: SimResult,
    summaries: dict,
    stress_survived: bool,
    winner_count: int,
    *,
    nw_lo: float,
    nw_hi: float,
    min_emergency: float,
    avg_dsr: float,
    dsr_cap: float = 0.30,
) -> dict:
    nw10 = summaries.get("year_10", {}).get("net_worth_real", summaries.get("max_net_worth_real", 0.0))
    components = {
        "net_worth_real": WEIGHTS["net_worth_real"] * _norm(nw10, nw_lo, nw_hi),
        "emergency": WEIGHTS["emergency"] * min(min_emergency / 6.0, 1.0),
        "dsr": WEIGHTS["dsr"] * (1.0 - min(avg_dsr / dsr_cap, 1.0)) if dsr_cap > 0 else 0.0,
        "stress": WEIGHTS["stress"] * (1.0 if stress_survived else 0.0),
        "robust": WEIGHTS["robust"] * (winner_count / 3.0),
    }
    total = sum(components.values())
    return {
        "total": round(total, 4),
        "components": {k: round(v, 4) for k, v in components.items()},
        "inputs": {
            "net_worth_real_y10": nw10,
            "min_emergency_months": min_emergency,
            "avg_dsr": avg_dsr,
            "stress_survived": stress_survived,
            "winner_count": winner_count,
        },
    }


def score_twin(
    cfg: TwinConfig, result: SimResult, stress_survived: bool = True, winner_count: int = 0
) -> float:
    """Skor cepat tanpa normalisasi lintas-twin (rentang asumsi tetap)."""
    s = summary(result)
    nw10 = s.get("year_10", {}).get("net_worth_real", 0.0)
    min_em = s.get("min_emergency_months", 0.0)
    avg_dsr = s.get("avg_dsr", 0.0)
    nw_component = WEIGHTS["net_worth_real"] * _norm(nw10, 0.0, 500_000_000.0)
    total = (
        nw_component
        + WEIGHTS["emergency"] * min(min_em / 6.0, 1.0)
        + WEIGHTS["dsr"] * (1.0 - min(avg_dsr / 0.30, 1.0))
        + WEIGHTS["stress"] * (1.0 if stress_survived else 0.0)
        + WEIGHTS["robust"] * (winner_count / 3.0)
    )
    return total


def hard_rule_excluded(s: dict) -> bool:
    """True jika twin melanggar aturan keras (macet / DSR>30% > 6 bulan)."""
    return bool(s.get("defaulted_months", 0) > 0 or s.get("dsr_over_months", 0) > 6)


def rank_twins(
    results: dict[str, SimResult],
    stress_by_twin: dict[str, bool],
    preset_wins: dict[str, int],
    dsr_cap: float = 0.30,
) -> tuple[str, dict[str, dict]]:
    """Rangking semua twin dan kembalikan kode terbaik + breakdown per twin."""
    summaries = {code: summary(res) for code, res in results.items()}

    nws = [summaries[c].get("year_10", {}).get("net_worth_real", 0.0) for c in results]
    nw_lo = min(nws) if nws else 0.0
    nw_hi = max(nws) if nws else 1.0
    if abs(nw_hi - nw_lo) < 1e-6:
        nw_lo, nw_hi = nw_lo - 1.0, nw_hi + 1.0

    breakdowns: dict[str, dict] = {}
    for code, res in results.items():
        s = summaries[code]
        breakdowns[code] = score_breakdown(
            res,
            s,
            stress_by_twin.get(code, True),
            preset_wins.get(code, 0),
            nw_lo=nw_lo,
            nw_hi=nw_hi,
            min_emergency=s.get("min_emergency_months", 0.0),
            avg_dsr=s.get("avg_dsr", 0.0),
            dsr_cap=dsr_cap,
        )

    # aturan keras + baseline tidak boleh menjadi rekomendasi.
    # Baseline ("0") = "tanpa perubahan"; rekomendasi harus berupa aksi konkret.
    excluded = {c: hard_rule_excluded(summaries[c]) for c in results}
    for c, is_excluded in excluded.items():
        if is_excluded:
            breakdowns[c]["deleted_by_hard_rule"] = True
    candidates = [c for c in results if not excluded[c] and c != "0"]
    if not candidates:
        # semua twin keputusan melanggar -> jatuh ke semua twin keputusan
        candidates = [c for c in results if c != "0"]
        for c in candidates:
            breakdowns[c]["hard_rule_overridden"] = True
            breakdowns[c]["deleted_by_hard_rule"] = False
    if not candidates:
        # hanya baseline tersedia
        candidates = list(results.keys())

    best = max(candidates, key=lambda c: breakdowns[c]["total"])
    return best, breakdowns
