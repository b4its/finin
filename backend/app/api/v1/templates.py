"""Endpoint template keputusan."""

from __future__ import annotations

from fastapi import APIRouter

from app.engine.templates import decision_templates

router = APIRouter()


@router.get("")
async def list_templates() -> dict:
    return {"templates": decision_templates()}
