"""Health check endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings
from app.engine.assumptions import load_assumptions

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    a = load_assumptions()
    return {
        "status": "ok",
        "time": datetime.now(UTC).isoformat(),
        "engine_version": settings.engine_version,
        "assumption_set": a.code,
        "llm_enabled": settings.llm_enabled,
    }
