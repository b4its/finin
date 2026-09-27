"""Endpoint set asumsi: default + sumber + tanggal."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.engine.assumptions import load_assumptions
from app.engine.regulatory import regulatory_payload

router = APIRouter()


@router.get("/default")
async def default_assumptions(preset: str = Query("moderat")) -> dict:
    a = load_assumptions()
    return {
        "code": a.code,
        "as_of": a.as_of,
        "label": a.label,
        "engine_version": a.engine_version,
        "preset": preset,
        "values": a.preset(preset),
        "presets": a.presets,
        "common": a.common,
        "regulatory": regulatory_payload(a.regulatory),
        "sources": a.sources,
        "market_context": a.market_context,
        "presets_available": list(a.presets.keys()),
    }
