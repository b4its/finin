"""Skema output API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class FlagOut(BaseModel):
    level: str
    code: str
    msg: str


class YearPoint(BaseModel):
    year: int
    net_worth: float
    net_worth_real: float
    debt: float
    cash: float
    invest: float
    cashflow: float
    emergency_months: float
    dsr: float
    defaulted: bool


class TwinSummary(BaseModel):
    year: int
    net_worth: float
    net_worth_real: float
    debt: float
    emergency_months: float
    avg_dsr: float
    defaulted: bool


class StressResult(BaseModel):
    shock: str
    label: str
    survived: bool
    min_cash: float
    new_debt: float
    worst_month: int
    note: str


class TwinOut(BaseModel):
    code: str
    label: str
    color: str
    dash: str
    icon: str
    description: str = ""
    config: dict[str, Any] = {}
    yearly_series: list[YearPoint] = []
    summary: dict[str, Any] = {}
    flags: list[FlagOut] = []
    stress: list[StressResult] = []
    score: float = 0.0
    score_breakdown: dict[str, Any] = {}
    deleted_by_hard_rule: bool = False


class SimulationResponse(BaseModel):
    id: str
    engine_version: str
    assumption_code: str
    assumption_as_of: str
    preset: str
    horizon_months: int
    twins: list[TwinOut]
    robust: bool
    robust_reason: str = ""
    preset_winners: dict[str, str] = {}
    assumptions: dict[str, Any] = {}
    market_context: list[dict[str, Any]] = []
    flags: list[FlagOut] = []
    best_twin: str = "0"
    sensitivity_drivers: list[str] = []


class RecommendationOut(BaseModel):
    simulation_id: str
    best_twin: str
    best_label: str
    first_step: str
    rationale: str
    score_breakdown: dict[str, Any]
    source: str  # 'llm' | 'template'


class NarrativeChunk(BaseModel):
    twin: str
    horizon: int
    text: str
    source: str
