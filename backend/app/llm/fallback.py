"""Fallback narasi berbasis template — dipakai saat LLM gagal / disabled / invalid."""

from __future__ import annotations


def rp(x: float) -> str:
    return f"Rp{x:,.0f}".replace(",", ".")


def fmt_months(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def rp_brief(x: float) -> str:
    ax = abs(x)
    if ax >= 1e9:
        return f"Rp{x / 1e9:.1f} miliar".replace(".", ",")
    if ax >= 1e6:
        return f"Rp{x / 1e6:.1f} jt".replace(".", ",")
    return rp(x)


def _flags_note(flags: list[dict]) -> str:
    if not flags:
        return ""
    red = [f for f in flags if f["level"] == "red"]
    slik = [f for f in flags if f["code"] == "SLIK_DEFAULT"]
    if red:
        return " Ada bendera: indikasi di atas batas OJK."
    if slik:
        return " Ada penanda: tercatat di SLIK OJK."
    return ""


def narrative_for_twin(twin: dict, baseline: dict | None = None) -> list[dict]:
    """Buat narasi horizon 5/10/20 untuk satu twin dari angka engine."""
    series = {p["year"]: p for p in twin.get("yearly_series", [])}
    base_series = {p["year"]: p for p in (baseline or {}).get("yearly_series", [])}
    flags = twin.get("flags", [])
    label = twin.get("label", twin.get("code"))
    notes = _flags_note(flags)
    out: list[dict] = []
    for y in (5, 10, 20):
        p = series.get(y)
        if p is None:
            continue
        parts = [f"Tahun ke-{y}: {label} punya net worth {rp_brief(p['net_worth'])}"]
        if p.get("debt", 0) > 1000:
            parts.append(f"dengan sisa utang {rp_brief(p['debt'])}")
        parts.append(f"dan dana darurat sekitar {fmt_months(p['emergency_months'])} bulan")
        bp = base_series.get(y)
        if bp:
            diff = p["net_worth"] - bp["net_worth"]
            if abs(diff) > 100_000:
                arah = "lebih tinggi" if diff > 0 else "lebih rendah"
                parts.append(f"({rp_brief(abs(diff))} {arah} dari baseline)")
        text = ", ".join(parts) + "." + notes
        out.append({"twin": twin.get("code"), "horizon": y, "text": text, "source": "template"})
    return out


def recommendation_fallback(best: dict, others: list[dict], robust: bool) -> dict:
    """Template rekomendasi."""
    s = best.get("summary", {})
    label = best.get("label", best.get("code"))
    nw10 = s.get("year_10", {}).get("net_worth_real", 0)
    first_step = f"Jalankan langkah '{label}': sisihkan dananya bulan ini sebelum belanja."

    if best.get("meta", {}).get("kind") in ("pinjol", "paylater") or best.get("code") == "B":
        first_step = "Buat rekening terpisah dan sisihkan tabungan bulanan secara otomatis sebelum belanja."
    elif best.get("code") in ("C", "D"):
        first_step = "Tulis rencana 12 bulan: daftar kursus atau kampus, biaya, dan target penghasilan."
    elif best.get("code") in ("E", "F"):
        first_step = "Hitung pengeluaran bulanan, lalu isi dana darurat sampai target beberapa bulan."
    elif best.get("code") == "G":
        first_step = (
            "Kunci tabungan DP di instrumen berisiko rendah dan pastikan cicilan KPR di bawah 30% gaji."
        )
    elif best.get("code") == "H":
        first_step = (
            "Siapkan rekening autodebet investasi bulanan untuk menyalurkan selisih biaya sewa vs cicilan."
        )
    elif best.get("code") == "I":
        first_step = (
            "Siapkan rekening autodebet cicilan kendaraan dan disiplin bayar sebelum jatuh tempo agar skor SLIK OJK tetap prima."
        )
    elif best.get("code") == "J":
        first_step = (
            "Cari unit kendaraan bekas terinspeksi, dan langsung alihkan selisih cicilan bulanan ke reksadana/saham tiap tanggal gajian."
        )

    alasan = (
        f"{label} menghasilkan nilai riil tahun ke-10 sekitar {rp_brief(nw10)} "
        f"dengan dana darurat minimum {fmt_months(s.get('min_emergency_months', 0))} bulan."
    )
    if others:
        pembanding = others[0].get("label", others[0].get("code"))
        alasan += f" Dibanding {pembanding}, proyeksi ini lebih stabil terhadap asumsi."
    if robust:
        alasan += " Kesimpulan ini konsisten di ketiga preset (robust)."
    else:
        alasan += " Hasilnya bergantung asumsi, jadi cek kembali preset lain."

    return {"first_step": first_step, "rationale": alasan, "source": "template"}
