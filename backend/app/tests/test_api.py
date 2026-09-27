"""Test integrasi API (pytest + httpx).

Butuh PostgreSQL (docker compose db). Jika DB tidak tersedia, test di-skip
otomatis lewat fixture `client`.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.db import Base, get_session
from app.main import app

TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not TEST_DB_URL, reason="TEST_DATABASE_URL tidak diset")


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(TEST_DB_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with Session() as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


SAMPLE = {
    "profile": {
        "age": 22,
        "income_type": "salary",
        "income_monthly": 6_000_000,
        "income_range": None,
        "expense_monthly": 3_800_000,
        "dependents_monthly": 500_000,
        "savings": 5_000_000,
        "existing_debt": {"principal": 0, "monthly_payment": 0},
    },
    "decisions": [
        {
            "type": "loan_vs_save",
            "loan": {"kind": "pinjol", "amount": 2_000_000, "tenor_months": 3, "rate_daily": 0.003},
            "save": {"monthly": 500_000, "instrument": "money_market"},
        }
    ],
    "preset": "moderat",
    "assumption_overrides": {},
}


async def test_health(client: AsyncClient):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["assumption_set"] == "ID-2026-09"


async def test_assumptions_default(client: AsyncClient):
    r = await client.get("/api/v1/assumptions/default")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "ID-2026-09"
    assert "regulatory" in body
    assert body["regulatory"]["version"] == "SEOJK-19-2025"
    assert body["regulatory"]["dsr_cap"] == 0.30
    assert "sources" in body
    assert len(body["sources"]) > 5


async def test_templates(client: AsyncClient):
    r = await client.get("/api/v1/templates")
    assert r.status_code == 200
    types = {t["type"] for t in r.json()["templates"]}
    assert types == {
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
    }


async def test_simulation_kpr_vs_rent(client: AsyncClient):
    payload = {
        "profile": {
            "age": 28,
            "income_type": "salary",
            "income_monthly": 15_000_000,
            "expense_monthly": 6_000_000,
            "dependents_monthly": 1_000_000,
            "savings": 150_000_000,
        },
        "decisions": [
            {
                "type": "kpr_vs_rent",
                "kpr": {
                    "property_price": 500_000_000,
                    "down_payment_pct": 0.20,
                    "interest_rate_annual": 0.08,
                    "tenor_years": 15,
                    "property_appreciation_annual": 0.04,
                },
                "rent": {
                    "rent_monthly": 2_500_000,
                    "invest_instrument": "bond",
                },
            }
        ],
        "preset": "moderat",
    }
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    data = r.json()
    twin_codes = {t["code"] for t in data["twins"]}
    assert "0" in twin_codes
    assert "G" in twin_codes
    assert "H" in twin_codes


async def test_regulatory_check_above_cap(client: AsyncClient):
    r = await client.post(
        "/api/v1/regulatory/check",
        json={
            "kind": "pinjol",
            "amount": 2_000_000,
            "tenor_months": 3,
            "rate_daily": 0.006,
            "income_monthly": 6_000_000,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert any(f["code"] == "ABOVE_OJK_CAP" for f in body["flags"])


async def test_regulatory_check_at_cap(client: AsyncClient):
    r = await client.post(
        "/api/v1/regulatory/check",
        json={
            "kind": "pinjol",
            "amount": 1_000_000,
            "tenor_months": 6,
            "rate_daily": 0.003,
            "income_monthly": 10_000_000,
        },
    )
    assert r.status_code == 200
    assert all(f["code"] != "ABOVE_OJK_CAP" for f in r.json()["flags"])


async def test_create_and_get_simulation(client: AsyncClient):
    r = await client.post("/api/v1/simulations", json=SAMPLE)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"]
    codes = [t["code"] for t in body["twins"]]
    assert codes == ["0", "A", "B"]
    assert "robust" in body

    sim_id = body["id"]
    r2 = await client.get(f"/api/v1/simulations/{sim_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == sim_id
    assert len(r2.json()["twins"]) == 3


async def test_create_simulation_dsr_flag(client: AsyncClient):
    payload = {
        "profile": {
            "age": 23,
            "income_type": "salary",
            "income_monthly": 3_000_000,
            "expense_monthly": 1_500_000,
            "savings": 0,
            "existing_debt": {"principal": 0, "monthly_payment": 0},
        },
        "decisions": [
            {
                "type": "loan_vs_save",
                "loan": {"kind": "pinjol", "amount": 4_000_000, "tenor_months": 3, "rate_daily": 0.003},
                "save": {"monthly": 200_000, "instrument": "money_market"},
            }
        ],
        "preset": "moderat",
    }
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    assert any(f["code"] == "DSR_OVER_30" for f in r.json()["flags"])


async def test_recompute(client: AsyncClient):
    r = await client.post("/api/v1/simulations", json=SAMPLE)
    sim_id = r.json()["id"]
    r2 = await client.post(f"/api/v1/simulations/{sim_id}/recompute", json={"preset": "konservatif"})
    assert r2.status_code == 200
    assert r2.json()["preset"] == "konservatif"


async def test_narrative_sse(client: AsyncClient):
    r = await client.post("/api/v1/simulations", json=SAMPLE)
    sim_id = r.json()["id"]
    r2 = await client.get(f"/api/v1/simulations/{sim_id}/narrative")
    assert r2.status_code == 200
    assert "data:" in r2.text
    assert '"done": true' in r2.text or '"done":true' in r2.text


async def test_recommendation(client: AsyncClient):
    r = await client.post("/api/v1/simulations", json=SAMPLE)
    sim_id = r.json()["id"]
    r2 = await client.get(f"/api/v1/simulations/{sim_id}/recommendation")
    assert r2.status_code == 200
    body = r2.json()
    assert body["best_twin"] != "0"  # baseline tidak boleh jadi rekomendasi
    assert body["first_step"]
    assert body["source"] in ("llm", "template")


async def test_events(client: AsyncClient):
    r = await client.post("/api/v1/simulations", json=SAMPLE)
    sim_id = r.json()["id"]
    r2 = await client.post(f"/api/v1/simulations/{sim_id}/events", json={"kind": "fsc_pre", "value": 3})
    assert r2.status_code == 201
    r3 = await client.post(f"/api/v1/simulations/{sim_id}/events", json={"kind": "fsc_post", "value": 5})
    assert r3.status_code == 201
    r4 = await client.post(f"/api/v1/simulations/{sim_id}/events", json={"kind": "commit"})
    assert r4.status_code == 201

    summary = await client.get("/api/v1/impact/summary")
    body = summary.json()
    assert body["fsc_pre_avg"] == 3.0
    assert body["fsc_post_avg"] == 5.0
    assert body["fsc_delta"] == 2.0
    assert body["commits"] == 1


async def test_invalid_id_404(client: AsyncClient):
    r = await client.get("/api/v1/simulations/not-a-uuid")
    assert r.status_code == 404


async def test_two_decisions_four_twins(client: AsyncClient):
    payload = dict(SAMPLE)
    payload["decisions"] = [
        SAMPLE["decisions"][0],
        {
            "type": "study_vs_work",
            "study": {"years": 2, "total_cost": 80_000_000, "part_time_work": False, "salary_premium": 0.15},
            "work": {"upskill_monthly": 300_000, "skill_premium": 0.10, "premium_after_months": 12},
        },
    ]
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    codes = [t["code"] for t in r.json()["twins"]]
    assert codes == ["0", "A", "B", "C", "D"]


async def test_manual_assumption_override(client: AsyncClient):
    """Edit manual asumsi harus mengubah hasil & tercermin di snapshot."""
    created = (await client.post("/api/v1/simulations", json=SAMPLE)).json()
    base_nw = [t["summary"]["year_10"]["net_worth"] for t in created["twins"] if t["code"] == "B"][0]

    rc = await client.post(
        f"/api/v1/simulations/{created['id']}/recompute",
        json={"assumption_overrides": {"inflation": 0.06, "returns": {"stock": 0.03}}},
    )
    assert rc.status_code == 200
    body = rc.json()
    assert body["assumptions"]["values"]["inflation"] == 0.06
    assert body["assumptions"]["values"]["returns"]["stock"] == 0.03
    assert body["assumptions"]["overrides"] == {"inflation": 0.06, "returns": {"stock": 0.03}}
    new_nw = [t["summary"]["year_10"]["net_worth"] for t in body["twins"] if t["code"] == "B"][0]
    # Inflasi lebih tinggi -> nilai riil lebih rendah (nominal berbeda juga)
    assert new_nw != base_nw

    # GET harus mempertahankan override
    got = (await client.get(f"/api/v1/simulations/{created['id']}")).json()
    assert got["assumptions"]["values"]["inflation"] == 0.06
    assert got["assumptions"]["overrides"]["inflation"] == 0.06


async def test_recompute_does_not_break_best_twin(client: AsyncClient):
    created = (await client.post("/api/v1/simulations", json=SAMPLE)).json()
    rc = await client.post(f"/api/v1/simulations/{created['id']}/recompute", json={"preset": "konservatif"})
    assert rc.status_code == 200
    assert rc.json()["preset"] == "konservatif"
    assert rc.json()["best_twin"] != "0"


async def test_get_round_trips_full_response(client: AsyncClient):
    """GET harus mengembalikan metadata yang sama seperti POST (reproducible)."""
    payload: dict = dict(SAMPLE)
    payload["horizon_months"] = 120
    created = (await client.post("/api/v1/simulations", json=payload)).json()
    got = (await client.get(f"/api/v1/simulations/{created['id']}")).json()

    assert got["horizon_months"] == 120
    assert got["robust_reason"] == created["robust_reason"]
    assert got["preset_winners"] == created["preset_winners"]
    assert got["preset"] == created["preset"]
    assert got["best_twin"] == created["best_twin"]
    assert got["sensitivity_drivers"] == created["sensitivity_drivers"]
    # warna & score_breakdown ikut tersimpan
    assert [t["color"] for t in got["twins"]] == [t["color"] for t in created["twins"]]
    assert all(t["score_breakdown"] for t in got["twins"])
    assert [t["code"] for t in got["twins"]] == [t["code"] for t in created["twins"]]
    # deleted_by_hard_rule konsisten antara POST dan GET
    assert [t["deleted_by_hard_rule"] for t in got["twins"]] == [
        t["deleted_by_hard_rule"] for t in created["twins"]
    ]


async def test_best_twin_consistent_across_endpoints(client: AsyncClient):
    """POST, GET, dan recommendation harus sepakat soal twin terbaik."""
    created = (await client.post("/api/v1/simulations", json=SAMPLE)).json()
    sim_id = created["id"]
    got = (await client.get(f"/api/v1/simulations/{sim_id}")).json()
    rec = (await client.get(f"/api/v1/simulations/{sim_id}/recommendation")).json()

    # best_twin bukan baseline dan bukan twin yang dilarang aturan keras
    assert created["best_twin"] != "0"
    assert got["best_twin"] == created["best_twin"]
    assert rec["best_twin"] == created["best_twin"]

    # skor best_twin = skor tertinggi di antara kandidat keputusan
    candidates = [t for t in got["twins"] if t["code"] != "0" and not t["deleted_by_hard_rule"]]
    top = max(candidates, key=lambda t: t["score"])
    assert top["code"] == created["best_twin"]
    # breakdown tersedia & berisi komponen berbobot
    assert "components" in rec["score_breakdown"]


async def test_tenor_boundary_via_api(client: AsyncClient):
    """Tenor tepat 6 bulan pakai cap 0,3%; tenor 7 bulan pindah ke 0,2%."""
    at6 = await client.post(
        "/api/v1/regulatory/check",
        json={
            "kind": "pinjol",
            "amount": 1_000_000,
            "tenor_months": 6,
            "rate_daily": 0.003,
            "income_monthly": 10_000_000,
        },
    )
    assert at6.json()["rate_cap_daily"] == 0.003
    assert all(f["code"] != "ABOVE_OJK_CAP" for f in at6.json()["flags"])

    at7 = await client.post(
        "/api/v1/regulatory/check",
        json={
            "kind": "pinjol",
            "amount": 1_000_000,
            "tenor_months": 7,
            "rate_daily": 0.003,
            "income_monthly": 10_000_000,
        },
    )
    assert at7.json()["rate_cap_daily"] == 0.002
    assert any(f["code"] == "ABOVE_OJK_CAP" for f in at7.json()["flags"])


async def test_edge_income_zero(client: AsyncClient):
    payload = {
        "profile": {
            "age": 20,
            "income_type": "allowance",
            "income_monthly": 0,
            "expense_monthly": 500_000,
            "savings": 0,
            "existing_debt": {"principal": 0, "monthly_payment": 0},
        },
        "decisions": [
            {"type": "emergency_vs_invest", "emergency": {"target_months": 6, "invest_monthly": 0}}
        ],
        "preset": "moderat",
    }
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    assert [t["code"] for t in r.json()["twins"]] == ["0", "E", "F"]


async def test_export_csv_and_json(client: AsyncClient):
    r = await client.post("/api/v1/simulations", json=SAMPLE)
    assert r.status_code == 201
    sim_id = r.json()["id"]

    # Test CSV export
    csv_res = await client.get(f"/api/v1/simulations/{sim_id}/export/csv")
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in csv_res.headers["content-disposition"]
    text_content = csv_res.text
    assert "Twin Code,Twin Label,Month,Year" in text_content
    assert "Net Worth Nominal" in text_content

    # Test JSON export
    json_res = await client.get(f"/api/v1/simulations/{sim_id}/export/json")
    assert json_res.status_code == 200
    assert json_res.headers["content-type"].startswith("application/json")
    json_data = json_res.json()
    assert json_data["id"] == sim_id
    assert "twins" in json_data
    assert "input" in json_data
    assert "exported_at" in json_data


async def test_api_vehicle_lease_vs_cash(client: AsyncClient):
    payload = {
        "profile": {
            "age": 25,
            "income_type": "salary",
            "income_monthly": 10_000_000,
            "expense_monthly": 4_500_000,
            "dependents_monthly": 0,
            "savings": 25_000_000,
            "existing_debt": {"principal": 0, "monthly_payment": 0},
        },
        "decisions": [
            {
                "type": "vehicle_lease_vs_cash",
                "vehicle_lease": {
                    "vehicle_price": 30_000_000,
                    "down_payment_pct": 0.20,
                    "interest_rate_annual": 0.12,
                    "tenor_months": 36,
                    "depreciation_annual": 0.15,
                },
                "vehicle_cash": {
                    "used_vehicle_price": 12_000_000,
                    "invest_instrument": "stock",
                },
            }
        ],
        "preset": "moderat",
    }
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    body = r.json()
    codes = [t["code"] for t in body["twins"]]
    assert "0" in codes
    assert "I" in codes
    assert "J" in codes


async def test_api_wedding_grand_vs_intimate(client: AsyncClient):
    payload = {
        "profile": {
            "age": 27,
            "income_type": "salary",
            "income_monthly": 15_000_000,
            "expense_monthly": 6_000_000,
            "dependents_monthly": 0,
            "savings": 50_000_000,
            "existing_debt": {"principal": 0, "monthly_payment": 0},
        },
        "decisions": [
            {
                "type": "wedding_grand_vs_intimate",
                "wedding_grand": {
                    "reception_cost": 200_000_000,
                    "savings_used": 50_000_000,
                    "loan_amount": 150_000_000,
                    "interest_rate_annual": 0.12,
                    "tenor_months": 36,
                },
                "wedding_intimate": {
                    "intimate_cost": 30_000_000,
                    "invest_instrument": "stock",
                },
            }
        ],
        "preset": "moderat",
    }
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    body = r.json()
    codes = [t["code"] for t in body["twins"]]
    assert "0" in codes
    assert "K" in codes
    assert "L" in codes
    # Twin L harus mengalahkan Twin K
    twin_k = next(t for t in body["twins"] if t["code"] == "K")
    twin_l = next(t for t in body["twins"] if t["code"] == "L")
    assert twin_l["score"] > twin_k["score"]


async def test_api_franchise_vs_passive_invest(client: AsyncClient):
    payload = {
        "profile": {
            "age": 28,
            "income_type": "salary",
            "income_monthly": 12_000_000,
            "expense_monthly": 5_000_000,
            "dependents_monthly": 0,
            "savings": 50_000_000,
            "existing_debt": {"principal": 0, "monthly_payment": 0},
        },
        "decisions": [
            {
                "type": "franchise_vs_passive_invest",
                "franchise": {
                    "franchise_fee": 80_000_000,
                    "savings_used": 30_000_000,
                    "kur_loan_amount": 50_000_000,
                    "kur_interest_rate_annual": 0.06,
                    "kur_tenor_months": 36,
                    "monthly_net_profit": 5_000_000,
                },
                "passive_invest": {
                    "invest_instrument": "bond",
                },
            }
        ],
        "preset": "moderat",
    }
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    body = r.json()
    codes = [t["code"] for t in body["twins"]]
    assert "0" in codes
    assert "M" in codes
    assert "N" in codes


async def test_api_child_education_unitlink_vs_diy(client: AsyncClient):
    payload = {
        "profile": {
            "age": 32,
            "income_type": "salary",
            "income_monthly": 16_000_000,
            "expense_monthly": 6_500_000,
            "dependents_monthly": 1_500_000,
            "savings": 50_000_000,
            "existing_debt": {"principal": 0, "monthly_payment": 0},
        },
        "decisions": [
            {
                "type": "child_education_unitlink_vs_diy",
                "child_education_unitlink": {
                    "monthly_premium": 2_000_000,
                    "target_years": 15,
                    "acquisition_fee_pct_y1": 0.60,
                    "acquisition_fee_pct_y2": 0.30,
                    "acquisition_fee_pct_y3": 0.15,
                    "invest_instrument": "stock",
                },
                "child_education_diy": {
                    "term_life_premium_monthly": 300_000,
                    "invest_instrument": "stock",
                },
            }
        ],
        "preset": "moderat",
    }
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    body = r.json()
    codes = [t["code"] for t in body["twins"]]
    assert "0" in codes
    assert "O" in codes
    assert "P" in codes


async def test_api_haji_furoda_vs_reguler(client: AsyncClient):
    payload = {
        "profile": {
            "age": 35,
            "income_type": "salary",
            "income_monthly": 20_000_000,
            "expense_monthly": 8_000_000,
            "dependents_monthly": 2_000_000,
            "savings": 80_000_000,
            "existing_debt": {"principal": 0, "monthly_payment": 0},
        },
        "decisions": [
            {
                "type": "haji_furoda_vs_reguler",
                "haji_furoda": {
                    "total_cost": 250_000_000,
                    "savings_used": 50_000_000,
                    "financing_amount": 200_000_000,
                    "financing_rate_annual": 0.09,
                    "tenor_months": 36,
                },
                "haji_reguler": {
                    "bpkh_initial_deposit": 25_000_000,
                    "invest_instrument": "bond",
                },
            }
        ],
        "preset": "moderat",
    }
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    body = r.json()
    codes = [t["code"] for t in body["twins"]]
    assert "0" in codes
    assert "Q" in codes
    assert "R" in codes


async def test_api_career_corporate_vs_freelance(client: AsyncClient):
    payload = {
        "profile": {
            "age": 27,
            "income_type": "salary",
            "income_monthly": 15_000_000,
            "expense_monthly": 6_000_000,
            "dependents_monthly": 0,
            "savings": 50_000_000,
            "existing_debt": {"principal": 0, "monthly_payment": 0},
        },
        "decisions": [
            {
                "type": "career_corporate_vs_freelance",
                "career_corporate": {
                    "salary_growth_annual": 0.06,
                    "bonus_months_annual": 2.0,
                },
                "career_freelance": {
                    "revenue_multiplier": 1.40,
                    "emergency_target_months": 9,
                    "bpjs_mandiri_monthly": 350_000,
                },
            }
        ],
        "preset": "moderat",
    }
    r = await client.post("/api/v1/simulations", json=payload)
    assert r.status_code == 201
    body = r.json()
    codes = [t["code"] for t in body["twins"]]
    assert "0" in codes
    assert "S" in codes
    assert "T" in codes




