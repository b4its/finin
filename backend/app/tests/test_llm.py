"""Test LLM guardrail: validator + fallback."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.llm import fallback
from app.llm.narrator import Narrator
from app.llm.validator import extract_numbers, numbers_from_facts, validate_numbers


def test_extract_numbers_id_format():
    nums = extract_numbers("Rp12.400.000 dan 6 bulan, 12,4%")
    assert "12400000" in nums
    assert "6" in nums
    assert "12.4" in nums


def test_numbers_from_facts():
    facts = {"a": "Rp2.000.000", "b": {"c": 6}, "d": ["Rp500.000"]}
    nums = numbers_from_facts(facts)
    assert "2000000" in nums
    assert "6" in nums
    assert "500000" in nums


def test_validate_valid_text():
    facts = {"nw": "Rp12.400.000", "months": "6 bulan"}
    ok, missing = validate_numbers("Net worth Rp12.400.000 dengan dana 6 bulan.", facts)
    assert ok
    assert missing == []


def test_validate_invalid_text():
    facts = {"nw": "Rp12.400.000"}
    ok, missing = validate_numbers("Net worth Rp99.999.999.", facts)
    assert not ok
    assert "99999999" in missing


def test_fallback_narrative_produces_all_horizons():
    twin = {
        "code": "B",
        "label": "Si Penabung",
        "flags": [],
        "yearly_series": [
            {
                "year": 5,
                "net_worth": 50_000_000,
                "net_worth_real": 45_000_000,
                "debt": 0,
                "emergency_months": 3.0,
            },
            {
                "year": 10,
                "net_worth": 100_000_000,
                "net_worth_real": 80_000_000,
                "debt": 0,
                "emergency_months": 5.0,
            },
            {
                "year": 20,
                "net_worth": 300_000_000,
                "net_worth_real": 200_000_000,
                "debt": 0,
                "emergency_months": 6.0,
            },
        ],
        "summary": {"avg_dsr": 0.05, "min_emergency_months": 3.0},
    }
    chunks = fallback.narrative_for_twin(twin)
    assert [c["horizon"] for c in chunks] == [5, 10, 20]
    assert all(c["source"] == "template" for c in chunks)


def test_fallback_recommendation():
    best = {
        "code": "B",
        "label": "Si Penabung",
        "summary": {"year_10": {"net_worth_real": 80_000_000}, "min_emergency_months": 5.0},
        "flags": [],
    }
    rec = fallback.recommendation_fallback(best, [], robust=True)
    assert rec["source"] == "template"
    assert rec["first_step"]
    assert rec["rationale"]


@pytest.mark.asyncio
async def test_narrator_disabled_uses_fallback():
    n = Narrator(enabled=False)
    twins = [
        {
            "code": "0",
            "label": "Kamu Tanpa Perubahan",
            "flags": [],
            "yearly_series": [
                {
                    "year": 5,
                    "net_worth": 10_000_000,
                    "net_worth_real": 9_000_000,
                    "debt": 0,
                    "emergency_months": 2.0,
                },
                {
                    "year": 10,
                    "net_worth": 20_000_000,
                    "net_worth_real": 17_000_000,
                    "debt": 0,
                    "emergency_months": 3.0,
                },
                {
                    "year": 20,
                    "net_worth": 40_000_000,
                    "net_worth_real": 30_000_000,
                    "debt": 0,
                    "emergency_months": 3.0,
                },
            ],
            "summary": {"avg_dsr": 0.0, "min_emergency_months": 2.0},
        }
    ]
    chunks = await n.narrate(twins)
    assert chunks
    assert all(c["source"] == "template" for c in chunks)


@pytest.mark.asyncio
async def test_narrator_hallucinated_numbers_fall_back():
    """LLM mengembalikan angka palsu -> harus fallback."""
    n = Narrator(enabled=True)
    twins = [
        {
            "code": "B",
            "label": "Si Penabung",
            "flags": [],
            "yearly_series": [
                {
                    "year": 5,
                    "net_worth": 50_000_000,
                    "net_worth_real": 45_000_000,
                    "debt": 0,
                    "emergency_months": 3.0,
                },
                {
                    "year": 10,
                    "net_worth": 100_000_000,
                    "net_worth_real": 80_000_000,
                    "debt": 0,
                    "emergency_months": 5.0,
                },
                {
                    "year": 20,
                    "net_worth": 300_000_000,
                    "net_worth_real": 200_000_000,
                    "debt": 0,
                    "emergency_months": 6.0,
                },
            ],
            "summary": {"avg_dsr": 0.05, "min_emergency_months": 3.0},
        }
    ]
    fake = '[{"twin": "B", "horizon": 5, "text": "Net worth Rp999.999.999 yang tidak ada di facts."}]'
    with patch.object(Narrator, "_call", new=AsyncMock(return_value=fake)):
        chunks = await n.narrate(twins)
    # semua fallback karena angka palsu
    assert all(c["source"] == "template" for c in chunks)


@pytest.mark.asyncio
async def test_narrator_valid_numbers_accepted():
    n = Narrator(enabled=True)
    twins = [
        {
            "code": "B",
            "label": "Si Penabung",
            "flags": [],
            "yearly_series": [
                {
                    "year": 5,
                    "net_worth": 50_000_000,
                    "net_worth_real": 45_000_000,
                    "debt": 0,
                    "emergency_months": 3.0,
                },
                {
                    "year": 10,
                    "net_worth": 100_000_000,
                    "net_worth_real": 80_000_000,
                    "debt": 0,
                    "emergency_months": 5.0,
                },
                {
                    "year": 20,
                    "net_worth": 300_000_000,
                    "net_worth_real": 200_000_000,
                    "debt": 0,
                    "emergency_months": 6.0,
                },
            ],
            "summary": {"avg_dsr": 0.05, "min_emergency_months": 3.0},
        }
    ]
    fake = '[{"twin": "B", "horizon": 5, "text": "Tahun ke-5 net worth Rp50.000.000, dana 3,0 bulan."}]'
    with patch.object(Narrator, "_call", new=AsyncMock(return_value=fake)):
        chunks = await n.narrate(twins)
    llm_chunks = [c for c in chunks if c["source"] == "llm"]
    assert len(llm_chunks) == 1
    assert llm_chunks[0]["horizon"] == 5
