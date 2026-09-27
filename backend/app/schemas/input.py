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
    existing_debt: ExistingDebt = Field(default_factory=lambda: ExistingDebt())

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


class KprDecision(BaseModel):
    property_price: float = Field(..., ge=0)
    down_payment_pct: float = Field(0.20, ge=0.05, le=0.90)
    interest_rate_annual: float = Field(0.08, ge=0.01, le=0.30)
    tenor_years: int = Field(15, ge=1, le=30)
    property_appreciation_annual: float = Field(0.04, ge=0, le=0.20)


class RentDecision(BaseModel):
    rent_monthly: float = Field(..., ge=0)
    invest_instrument: Instrument = "bond"


class VehicleLeaseDecision(BaseModel):
    vehicle_price: float = Field(..., ge=0)
    down_payment_pct: float = Field(0.20, ge=0.05, le=0.80)
    interest_rate_annual: float = Field(0.12, ge=0.01, le=0.35)
    tenor_months: int = Field(36, ge=6, le=72)
    depreciation_annual: float = Field(0.12, ge=0.02, le=0.30)


class VehicleCashDecision(BaseModel):
    used_vehicle_price: float = Field(..., ge=0)
    invest_instrument: Instrument = "stock"


class WeddingGrandDecision(BaseModel):
    reception_cost: float = Field(..., ge=0)
    savings_used: float = Field(..., ge=0)
    loan_amount: float = Field(0.0, ge=0)
    interest_rate_annual: float = Field(0.12, ge=0.01, le=0.35)
    tenor_months: int = Field(36, ge=6, le=60)


class WeddingIntimateDecision(BaseModel):
    intimate_cost: float = Field(..., ge=0)
    invest_instrument: Instrument = "stock"


class FranchiseDecision(BaseModel):
    franchise_fee: float = Field(..., ge=0)
    savings_used: float = Field(..., ge=0)
    kur_loan_amount: float = Field(0.0, ge=0)
    kur_interest_rate_annual: float = Field(0.06, ge=0.01, le=0.25)
    kur_tenor_months: int = Field(36, ge=6, le=60)
    monthly_net_profit: float = Field(..., ge=0)


class PassiveInvestDecision(BaseModel):
    invest_instrument: Instrument = "bond"


class ChildEducationUnitLinkDecision(BaseModel):
    monthly_premium: float = Field(..., ge=200_000)
    target_years: int = Field(15, ge=5, le=20)
    acquisition_fee_pct_y1: float = Field(0.60, ge=0.10, le=0.90)
    acquisition_fee_pct_y2: float = Field(0.30, ge=0.00, le=0.60)
    acquisition_fee_pct_y3: float = Field(0.15, ge=0.00, le=0.40)
    invest_instrument: Instrument = "stock"


class ChildEducationDiyDecision(BaseModel):
    term_life_premium_monthly: float = Field(250_000, ge=50_000)
    invest_instrument: Instrument = "stock"


class HajiFurodaDecision(BaseModel):
    total_cost: float = Field(..., ge=50_000_000)
    savings_used: float = Field(..., ge=0)
    financing_amount: float = Field(0.0, ge=0)
    financing_rate_annual: float = Field(0.09, ge=0.01, le=0.25)
    tenor_months: int = Field(36, ge=12, le=60)


class HajiRegulerDecision(BaseModel):
    bpkh_initial_deposit: float = Field(25_000_000, ge=25_000_000)
    invest_instrument: Instrument = "bond"


class CareerCorporateDecision(BaseModel):
    salary_growth_annual: float = Field(0.06, ge=0.01, le=0.20)
    bonus_months_annual: float = Field(1.5, ge=0.0, le=6.0)


class CareerFreelanceDecision(BaseModel):
    revenue_multiplier: float = Field(1.40, ge=1.0, le=3.0)
    emergency_target_months: int = Field(9, ge=6, le=18)
    bpjs_mandiri_monthly: float = Field(350_000, ge=100_000)


class Decision(BaseModel):
    type: Literal[
        "loan_vs_save",
        "study_vs_work",
        "emergency_vs_invest",
        "kpr_vs_rent",
        "vehicle_lease_vs_cash",
        "wedding_grand_vs_intimate",
        "franchise_vs_passive_invest",
        "child_education_unitlink_vs_diy",
        "haji_furoda_vs_reguler",
        "career_corporate_vs_freelance",
    ]
    loan: LoanDecision | None = None
    save: SaveDecision | None = None
    study: StudyDecision | None = None
    work: WorkDecision | None = None
    emergency: EmergencyDecision | None = None
    kpr: KprDecision | None = None
    rent: RentDecision | None = None
    vehicle_lease: VehicleLeaseDecision | None = None
    vehicle_cash: VehicleCashDecision | None = None
    wedding_grand: WeddingGrandDecision | None = None
    wedding_intimate: WeddingIntimateDecision | None = None
    franchise: FranchiseDecision | None = None
    passive_invest: PassiveInvestDecision | None = None
    child_education_unitlink: ChildEducationUnitLinkDecision | None = None
    child_education_diy: ChildEducationDiyDecision | None = None
    haji_furoda: HajiFurodaDecision | None = None
    haji_reguler: HajiRegulerDecision | None = None
    career_corporate: CareerCorporateDecision | None = None
    career_freelance: CareerFreelanceDecision | None = None

    @model_validator(mode="after")
    def _require_payload(self) -> Decision:
        if self.type == "loan_vs_save" and (self.loan is None or self.save is None):
            raise ValueError("loan_vs_save butuh 'loan' dan 'save'")
        if self.type == "study_vs_work" and (self.study is None or self.work is None):
            raise ValueError("study_vs_work butuh 'study' dan 'work'")
        if self.type == "emergency_vs_invest" and self.emergency is None:
            raise ValueError("emergency_vs_invest butuh 'emergency'")
        if self.type == "kpr_vs_rent" and (self.kpr is None or self.rent is None):
            raise ValueError("kpr_vs_rent butuh 'kpr' dan 'rent'")
        if self.type == "vehicle_lease_vs_cash" and (self.vehicle_lease is None or self.vehicle_cash is None):
            raise ValueError("vehicle_lease_vs_cash butuh 'vehicle_lease' dan 'vehicle_cash'")
        if self.type == "wedding_grand_vs_intimate" and (
            self.wedding_grand is None or self.wedding_intimate is None
        ):
            raise ValueError("wedding_grand_vs_intimate butuh 'wedding_grand' dan 'wedding_intimate'")
        if self.type == "franchise_vs_passive_invest" and (
            self.franchise is None or self.passive_invest is None
        ):
            raise ValueError("franchise_vs_passive_invest butuh 'franchise' dan 'passive_invest'")
        if self.type == "child_education_unitlink_vs_diy" and (
            self.child_education_unitlink is None or self.child_education_diy is None
        ):
            raise ValueError(
                "child_education_unitlink_vs_diy butuh 'child_education_unitlink' dan 'child_education_diy'"
            )
        if self.type == "haji_furoda_vs_reguler" and (
            self.haji_furoda is None or self.haji_reguler is None
        ):
            raise ValueError("haji_furoda_vs_reguler butuh 'haji_furoda' dan 'haji_reguler'")
        if self.type == "career_corporate_vs_freelance" and (
            self.career_corporate is None or self.career_freelance is None
        ):
            raise ValueError(
                "career_corporate_vs_freelance butuh 'career_corporate' dan 'career_freelance'"
            )
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
