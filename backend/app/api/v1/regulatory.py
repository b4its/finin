"""Endpoint cek regulasi OJK langsung (dipakai wizard saat mengetik)."""

from __future__ import annotations

from fastapi import APIRouter

from app.engine.assumptions import load_assumptions
from app.engine.regulatory import cap_for, check_pinjol, installment_for, regulatory_payload
from app.schemas.input import RegulatoryCheckRequest

router = APIRouter()


@router.post("/check")
async def check(payload: RegulatoryCheckRequest) -> dict:
    a = load_assumptions()
    ruleset = a.ruleset()
    flags = check_pinjol(
        amount=payload.amount,
        tenor_months=payload.tenor_months,
        rate_daily=payload.rate_daily,
        income_monthly=payload.income_monthly,
        existing_payment=payload.existing_payment,
        penalty_daily=payload.penalty_daily,
        ruleset=ruleset,
    )
    rate_cap, penalty_cap = cap_for(payload.tenor_months, ruleset)
    installment = installment_for(payload.amount, payload.rate_daily, payload.tenor_months, ruleset)
    dsr = (
        (installment + payload.existing_payment) / payload.income_monthly
        if payload.income_monthly > 0
        else 0.0
    )
    return {
        "flags": [f.to_dict() for f in flags],
        "rate_cap_daily": rate_cap,
        "penalty_cap_daily": penalty_cap,
        "installment": installment,
        "dsr": dsr,
        "dsr_cap": ruleset["dsr_cap"],
        "ruleset": regulatory_payload(a.regulatory),
    }
