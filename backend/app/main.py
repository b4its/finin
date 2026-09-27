"""FastAPI app entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings

app = FastAPI(
    title="Financial Twin API",
    version=settings.engine_version,
    description="Decision-support system: deterministic engine + Regulatory Guard OJK + LLM narrator.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": str(exc), "detail": {}},
    )


@app.get("/")
async def root() -> dict:
    return {
        "name": "Financial Twin API",
        "version": settings.engine_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
