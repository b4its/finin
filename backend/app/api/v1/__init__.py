"""Router agregat untuk API v1."""

from fastapi import APIRouter

from app.api.v1 import assumptions, events, health, regulatory, simulations, templates

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(assumptions.router, prefix="/assumptions", tags=["assumptions"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(regulatory.router, prefix="/regulatory", tags=["regulatory"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["simulations"])
api_router.include_router(events.router, tags=["events"])
