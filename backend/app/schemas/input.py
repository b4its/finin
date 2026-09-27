"""Skema input (Pydantic) untuk API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

PresetName = Literal["konservatif", "moderat", "optimis"]
IncomeType = Literal["salary", "allowance", "variable"]
Instrument = Literal["savings", "deposit", "money_market", "bond", "stock"]


class ExistingDebt(BaseModel):
    principal: float = Field(0, ge=0)
    monthly_payment: float = Field(0, ge=0)
    annual_rate: float = Field(0.0, ge=0)
    tenor_months: int = Field(0, ge=0)


class IncomeRange(BaseModel):
    min: float = Field(..., ge=0)
    max: float = Field(..., ge=0)

    @model_validator(mode="after")
    def _check(self) -> IncomeRange:
        if self.max < self.min:
            self.min, self.max = self.max, self.min
        return self


class Profile(BaseModel):
    age: int = Field(..., ge=15, le=60)
    income_type: IncomeType = "salary"
    income_monthly: float = Field(..., ge=0)
    income_range: IncomeRange | None = None
    expense_monthly: float = Field(..., ge=0)
    dependents_monthly: float = Field(0, ge=0)
    savings: float = Field(0, ge=0)
    existing_debt: ExistingDebt = Field(default_factory=ExistingDebt)

    @model_validator(mode="after")
    def _check_range(self) -> Profile:
        if self.income_type == "variable" and self.income_range is None:
            self.income_range = IncomeRange(min=self.income_monthly, max=self.income_monthly)
        return self


class LoanDecision(BaseModel):
    kind: Literal["pinjol", "paylater"] = "pinjol"
    amount: float = Field(..., ge=0)
    tenor_months: int = Field(..., ge=1, le=60)
    rate_daily: float = Field(..., ge=0)
    penalty_daily: float | None = Field(default=None, ge=0)


class SaveDecision(BaseModel):
    monthly: float = Field(0, ge=0)
    instrument: Instrument = "money_market"


class StudyDecision(BaseModel):
    years: int = Field(2, ge=1, le=6)
    total_cost: float = Field(0, ge=0)
    part_time_work: bool = False
    part_time_monthly: float = Field(0, ge=0)
    salary_premium: float = Field(0.15, ge=0, le=1.0)


class WorkDecision(BaseModel):
    upskill_monthly: float = Field(300_000, ge=0)
    skill_premium: float = Field(0.10, ge=0, le=1.0)
    premium_after_months: int = Field(12, ge=1, le=60)


class EmergencyDecision(BaseModel):
    target_months: int = Field(6, ge=1, le=12)
    invest_monthly: float = Field(0, ge=0)


class Decision(BaseModel):
    type: Literal["loan_vs_save", "study_vs_work", "emergency_vs_invest"]
    loan: LoanDecision | None = None
    save: SaveDecision | None = None
    study: StudyDecision | None = None
    work: WorkDecision | None = None
    emergency: EmergencyDecision | None = None

    @model_validator(mode="after")
    def _require_payload(self) -> Decision:
        if self.type == "loan_vs_save" and (self.loan is None or self.save is None):
            raise ValueError("loan_vs_save butuh 'loan' dan 'save'")
        if self.type == "study_vs_work" and (self.study is None or self.work is None):
            raise ValueError("study_vs_work butuh 'study' dan 'work'")
        if self.type == "emergency_vs_invest" and self.emergency is None:
            raise ValueError("emergency_vs_invest butuh 'emergency'")
        return self


class SimulationRequest(BaseModel):
    profile: Profile
    decisions: list[Decision] = Field(..., min_length=1, max_length=2)
    preset: PresetName = "moderat"
    assumption_overrides: dict[str, Any] = Field(default_factory=dict)
    horizon_months: int = Field(240, ge=12, le=360)

    @field_validator("decisions")
    @classmethod
    def _unique_types(cls, v: list[Decision]) -> list[Decision]:
        types = [d.type for d in v]
        if len(set(types)) != len(types):
            raise ValueError("Setiap tipe keputusan hanya boleh dipilih sekali")
        return v


class RecomputeRequest(BaseModel):
    preset: PresetName | None = None
    assumption_overrides: dict[str, Any] = Field(default_factory=dict)


class RegulatoryCheckRequest(BaseModel):
    kind: Literal["pinjol", "paylater"] = "pinjol"
    amount: float = Field(..., ge=0)
    tenor_months: int = Field(..., ge=1, le=60)
    rate_daily: float = Field(..., ge=0)
    penalty_daily: float | None = Field(default=None, ge=0)
    income_monthly: float = Field(0, ge=0)
    existing_payment: float = Field(0, ge=0)


class EventRequest(BaseModel):
    kind: Literal["fsc_pre", "fsc_post", "commit"]
    value: int | None = Field(default=None, ge=1, le=7)
