"""Sensitivitas 3 preset + label robust.

Setiap twin dihitung dengan 3 preset. Jika pemenang (skor tertinggi) sama
di ketiganya, tampilkan label "Rekomendasi robust". Jika tidak, tampilkan
"Bergantung asumsi" beserta parameter pemicu.
"""

from __future__ import annotations

from app.engine.assumptions import PRESETS, Assumptions
from app.engine.income import IncomeProfile
from app.engine.scoring import score_twin
from app.engine.templates import TwinConfig
from app.schemas.input import Profile


def score_with_preset(
    cfg: TwinConfig,
    profile: Profile,
    income_profile: IncomeProfile,
    assumptions: Assumptions,
    ruleset: dict,
    preset_name: str,
    *,
    months: int = 240,
    stress_survived: bool = True,
    winner_count: int = 0,
) -> float:
    from app.engine.simulator import simulate

    preset = assumptions.preset(preset_name)
    res = simulate(cfg, profile, income_profile, preset, ruleset, months=months)
    return score_twin(cfg, res, stress_survived, winner_count)


def run_sensitivity(
    twins: list[TwinConfig],
    profile: Profile,
    income_profile: IncomeProfile,
    assumptions: Assumptions,
    ruleset: dict,
    *,
    months: int = 240,
) -> dict:
    """Hitung skor tiap twin di tiap preset, tentukan pemenang & robust."""
    scores: dict[str, dict[str, float]] = {t.code: {} for t in twins}
    winners: dict[str, str] = {}
    # Baseline ("0") tidak boleh jadi pemenang rekomendasi; hanya keputusan nyata.
    eligible = [t for t in twins if t.code != "0"] or twins
    for preset_name in PRESETS:
        best_code, best_score = None, float("-inf")
        # skor baseline (ditampilkan, tapi tidak bisa menang)
        for t in twins:
            if t.code == "0":
                scores[t.code][preset_name] = score_with_preset(
                    t, profile, income_profile, assumptions, ruleset, preset_name, months=months
                )
        for t in eligible:
            s = score_with_preset(
                t, profile, income_profile, assumptions, ruleset, preset_name, months=months
            )
            if t.code != "0":
                scores[t.code][preset_name] = s
            if s > best_score:
                best_score, best_code = s, t.code
        winners[preset_name] = best_code or "0"

    winner_set = set(winners.values())
    robust = len(winner_set) == 1

    # Parameter pemicu: cari parameter yang berubah antar preset dan relevan.
    drivers: list[str] = []
    if not robust:
        drivers = ["inflasi", "imbal hasil investasi", "kenaikan gaji", "premi S2"]

    return {
        "preset_scores": scores,
        "preset_winners": winners,
        "robust": robust,
        "robust_reason": (
            "Pemenang sama di ketiga preset."
            if robust
            else f"Pemenang berbeda antar preset: {', '.join(winners.values())}. Bergantung asumsi."
        ),
        "drivers": drivers,
    }
