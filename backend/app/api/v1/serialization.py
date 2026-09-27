"""Serialisasi hasil simulasi ke bentuk yang bisa disimpan & dibaca ulang.

Digunakan oleh API dan seed script agar respons POST/GET identik (reproducible).
"""

from __future__ import annotations

from app.engine.runner import FullSimulation


def cfg_to_dict(cfg) -> dict:  # noqa: ANN001
    """Konfigurasi twin untuk disimpan (termasuk warna/ikon)."""
    return {
        "code": cfg.code,
        "label": cfg.label,
        "description": cfg.description,
        "_color": cfg.color,
        "_dash": cfg.dash,
        "_icon": cfg.icon,
        "role": cfg.meta.get("role", "decision"),
        "study": cfg.study,
        "emergency_first": cfg.emergency_first,
        "monthly_invest": cfg.monthly_invest,
        "instrument": cfg.instrument,
        "loan_kind": cfg.loan.kind if cfg.loan else None,
        "loan_principal": cfg.loan.principal if cfg.loan else 0,
        "meta": cfg.meta,
    }


def enriched_snapshot(a, full: FullSimulation) -> dict:  # noqa: ANN001
    """Snapshot asumsi + metadata agar GET bisa mereproduksi respons lengkap."""
    snap = a.to_dict(full.preset)
    snap["_meta"] = {
        "horizon_months": full.horizon_months,
        "robust_reason": full.robust_reason,
        "preset_winners": full.preset_winners,
        "input_flags": full.input_flags,
        "best_twin": full.best_twin,
        "sensitivity_drivers": full.sensitivity_drivers,
        "deleted_by_hard_rule": {t.cfg.code: t.deleted_by_hard_rule for t in full.twins},
    }
    return snap


def preset_scores_for(full: FullSimulation, code: str) -> dict:
    """Skor per preset + breakdown + flag aturan keras untuk satu twin."""
    twin = next((t for t in full.twins if t.cfg.code == code), None)
    ps: dict = dict(full.preset_scores.get(code) or {})
    if twin is not None:
        ps["_breakdown"] = twin.score_breakdown
        ps["_deleted_by_hard_rule"] = twin.deleted_by_hard_rule
    return ps
