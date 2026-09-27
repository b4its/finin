"""Endpoint kalkulator resmi PPh 21 TER (PP 58/2023) & BPJS Ketenagakerjaan/Kesehatan."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.engine.tax import (
    calculate_statutory_deductions,
    project_jht_wealth,
)

router = APIRouter()


class TaxCalculateRequest(BaseModel):
    gross_monthly: float = Field(..., ge=0, description="Penghasilan kotor bulanan (Rupiah)")
    ter_category: Literal["A", "B", "C"] = Field("A", description="Kategori TER sesuai PTKP")
    include_bpjs: bool = Field(True, description="Sertakan potongan BPJS TK dan Kesehatan")
    current_age: int = Field(25, ge=18, le=65, description="Usia saat ini untuk proyeksi JHT")


class TaxCalculateResponse(BaseModel):
    gross_monthly: float
    ter_category: str
    pph21_monthly: float
    pph21_effective_rate: float
    bpjs_jht_worker: float
    bpjs_jp_worker: float
    bpjs_kes_worker: float
    total_worker_deductions: float
    net_take_home_pay: float
    bpjs_jht_employer: float
    bpjs_jp_employer: float
    bpjs_kes_employer: float
    total_jht_monthly_savings: float
    jht_projection: dict


@router.post("/calculate", response_model=TaxCalculateResponse)
def calculate_tax_post(req: TaxCalculateRequest) -> TaxCalculateResponse:
    res = calculate_statutory_deductions(
        gross_monthly=req.gross_monthly,
        ter_category=req.ter_category,
        include_bpjs=req.include_bpjs,
    )
    jht_proj = project_jht_wealth(
        monthly_gross=req.gross_monthly,
        current_age=req.current_age,
    )
    return TaxCalculateResponse(
        **res.to_dict(),
        jht_projection=jht_proj,
    )


@router.get("/calculate", response_model=TaxCalculateResponse)
def calculate_tax_get(
    gross_monthly: float = Query(..., ge=0),
    ter_category: Literal["A", "B", "C"] = Query("A"),
    include_bpjs: bool = Query(True),
    current_age: int = Query(25, ge=18, le=65),
) -> TaxCalculateResponse:
    res = calculate_statutory_deductions(
        gross_monthly=gross_monthly,
        ter_category=ter_category,
        include_bpjs=include_bpjs,
    )
    jht_proj = project_jht_wealth(
        monthly_gross=gross_monthly,
        current_age=current_age,
    )
    return TaxCalculateResponse(
        **res.to_dict(),
        jht_projection=jht_proj,
    )
