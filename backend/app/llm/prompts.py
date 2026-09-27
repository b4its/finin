"""Prompt untuk narator LLM."""

from __future__ import annotations

SYSTEM_PROMPT = """Kamu adalah narator persona untuk aplikasi edukasi keuangan "Financial Twin".

Aturan WAJIB:
1. Pakai HANYA angka yang ada di FACTS. Jangan menghitung, jangan mengarang angka baru.
2. Jangan menyebut merek, produk, atau penyedia jasa keuangan apa pun.
3. Jangan menghakimi pengguna. Pakai bahasa netral ("konsekuensi", bukan "salah" atau "bodoh").
4. Bahasa Indonesia santai tapi jelas, maksimal 60 kata per horizon.
5. Jika twin punya bendera regulasi, sebutkan secara netral tanpa menakut-nakuti.
6. Jangan memberi nasihat keuangan atau investasi personal; ini proyeksi simulasi.

Format keluaran: JSON valid berisi array objek {"twin": "...", "horizon": 5|10|20, "text": "..."}.
"""

RECOMMENDATION_SYSTEM = """Kamu adalah penulis rekomendasi untuk aplikasi edukasi "Financial Twin".

Aturan WAJIB:
1. Pakai HANYA angka dari FACTS.
2. Jangan menyebut merek/produk/penyedia.
3. Jangan menghakimi; bahasa netral dan suportif.
4. "first_step" = satu aksi konkret yang bisa dikerjakan hari ini, maksimal 25 kata.
5. "rationale" = alasan komparatif vs twin lain, maksimal 80 kata, merujuk angka FACTS.
6. Ini simulasi edukatif, bukan nasihat keuangan personal.

Format keluaran: JSON valid {"first_step": "...", "rationale": "..."}.
"""


def facts_for_twin(twin: dict) -> dict:
    """Bangun ringkasan fakta yang dikirim ke LLM (angka sudah diformat)."""

    def rp(x: float) -> str:
        return f"Rp{x:,.0f}".replace(",", ".")

    s = twin.get("summary", {})
    series = {p["year"]: p for p in twin.get("yearly_series", [])}
    horizons = {}
    for y in (5, 10, 20):
        p = series.get(y)
        if p is None:
            continue
        horizons[y] = {
            "net_worth": rp(p["net_worth"]),
            "net_worth_real": rp(p["net_worth_real"]),
            "debt": rp(p["debt"]),
            "emergency_months": f"{p['emergency_months']:.1f} bulan".replace(".", ","),
        }
    return {
        "twin_code": twin.get("code"),
        "twin_label": twin.get("label"),
        "description": twin.get("description", ""),
        "horizons": horizons,
        "avg_dsr_pct": f"{s.get('avg_dsr', 0) * 100:.0f}%",
        "min_emergency_months": f"{s.get('min_emergency_months', 0):.1f} bulan".replace(".", ","),
        "flags": [{"level": f["level"], "code": f["code"]} for f in twin.get("flags", [])],
    }


def build_narrative_user_prompt(twins_facts: list[dict], baseline_facts: dict) -> str:
    import json

    return (
        "FACTS (baseline = 'Kamu Tanpa Perubahan'):\n"
        + json.dumps({"baseline": baseline_facts, "twins": twins_facts}, ensure_ascii=False, indent=2)
        + "\n\nTulis narasi per twin untuk horizon 5, 10, dan 20 tahun. "
        "Bandingkan dengan baseline bila relevan. Keluarkan JSON array."
    )


def build_recommendation_user_prompt(best_facts: dict, others_facts: list[dict], robust: bool) -> str:
    import json

    return (
        "FACTS:\n"
        + json.dumps(
            {"best": best_facts, "others": others_facts, "robust": robust},
            ensure_ascii=False,
            indent=2,
        )
        + '\n\nTulis {"first_step": ..., "rationale": ...} dalam JSON.'
    )
