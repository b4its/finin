"""Serialisasi hasil simulasi ke bentuk yang bisa disimpan & dibaca ulang.

Digunakan oleh API dan seed script agar respons POST/GET identik (reproducible).
"""

from __future__ import annotations

from app.engine.runner import FullSimulation


def cfg_to_dict(cfg) -> dict:  # noqa: ANN001
    """Konfigurasi twin untuk disimpan (termasuk warna/ikon).

    Menyertakan aset riil (nilai & penyusutan properti/kendaraan) agar UI
    (mis. Radar Alokasi Aset) dapat menghitung porsi aset fisik. Sebelumnya
    field ini tidak diserialisasi sehingga porsi aset riil selalu 0 di UI,
    padahal engine memakainya saat simulasi.
    """
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
        # Aset riil (dipakai UI alokasi aset; sebelumnya hilang dari snapshot).
        "property_initial_value": cfg.property_initial_value,
        "property_appreciation_annual": cfg.property_appreciation_annual,
        "vehicle_initial_value": cfg.vehicle_initial_value,
        "vehicle_depreciation_annual": cfg.vehicle_depreciation_annual,
        "meta": cfg.meta,
    }


def enriched_snapshot(a, full: FullSimulation) -> dict:  # noqa: ANN001
    """Snapshot asumsi + metadata agar GET bisa mereproduksi respons lengkap."""
    snap = a.to_dict(full.preset)
    # Refleksikan nilai efektif (setelah override manual) agar UI menampilkan
    # angka yang benar-benar dipakai engine.
    if full.effective_values:
        snap["values"] = full.effective_values
    snap["overrides"] = full.overrides
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
