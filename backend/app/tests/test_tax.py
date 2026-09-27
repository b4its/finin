"""Tests for Indonesian tax (PPh 21 TER PP 58/2023) and BPJS calculations."""

from __future__ import annotations

from httpx import AsyncClient

from app.engine.tax import (
    BPJS_KES_MAX_WAGE,
    BPJS_TK_JP_MAX_WAGE,
    calculate_statutory_deductions,
    project_jht_wealth,
    ter_rate_for,
)


def test_ter_rates_category_a():
    # <= 5.4 jt: 0%
    assert ter_rate_for(5_000_000, "A") == 0.0
    assert ter_rate_for(5_400_000, "A") == 0.0

    # 10 jt: 2%
    assert ter_rate_for(10_000_000, "A") == 0.02

    # 15 jt: 6%
    assert ter_rate_for(15_000_000, "A") == 0.06

    # 20 jt: 9%
    assert ter_rate_for(20_000_000, "A") == 0.09


def test_ter_rates_category_b_and_c():
    # Kategori B PTKP lebih tinggi (sampai 6.2 jt = 0%)
    assert ter_rate_for(6_000_000, "B") == 0.0
    assert ter_rate_for(10_000_000, "B") == 0.015

    # Kategori C PTKP tertinggi (sampai 6.6 jt = 0%)
    assert ter_rate_for(6_500_000, "C") == 0.0
    assert ter_rate_for(9_500_000, "C") == 0.0125
    assert ter_rate_for(10_000_000, "C") == 0.015


def test_calculate_statutory_deductions_full():
    gross = 15_000_000.0
    res = calculate_statutory_deductions(gross, "A", include_bpjs=True)

    # PPh 21: 15.000.000 * 6% = 900.000
    assert res.pph21_monthly == 900_000.0

    # JHT pekerja: 2% * 15.000.000 = 300.000
    assert res.bpjs_jht_worker == 300_000.0

    # JP pekerja: 1% * min(15 jt, 10.042.300) = 100.423
    assert res.bpjs_jp_worker == round(BPJS_TK_JP_MAX_WAGE * 0.01)

    # BPJS Kes: 1% * min(15 jt, 12.000.000) = 120.000
    assert res.bpjs_kes_worker == round(BPJS_KES_MAX_WAGE * 0.01)

    # Net Take-Home Pay harus lebih kecil dari gross
    assert res.net_take_home_pay < gross
    assert res.total_worker_deductions > 0
    assert res.net_take_home_pay == gross - res.total_worker_deductions

    # Total tabungan pensiun JHT bulanan (pekerja 2% + pemberi kerja 3.7% = 5.7%)
    assert res.total_jht_monthly_savings == round(gross * 0.057)


def test_project_jht_wealth():
    proj = project_jht_wealth(10_000_000, current_age=25, retirement_age=56)
    assert proj["years_to_retirement"] == 31
    assert proj["projected_jht_lump_sum"] > 500_000_000  # Compound growth over 31 years


async def test_api_tax_calculate():
    from httpx import ASGITransport

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/tax/calculate",
            json={
                "gross_monthly": 15_000_000,
                "ter_category": "A",
                "include_bpjs": True,
                "current_age": 26,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["gross_monthly"] == 15_000_000
        assert data["pph21_monthly"] == 900_000
        assert data["net_take_home_pay"] > 13_000_000
        assert "jht_projection" in data
        assert data["jht_projection"]["projected_jht_lump_sum"] > 0

