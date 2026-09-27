# Financial Twin 🌌

> Lihat dirimu di 5, 10, dan 20 tahun — sebelum kamu memutuskan.

**Financial Twin** adalah *decision-support system* yang membuat "kembaran digital" finansial pengguna
di 3–4 skenario masa depan paralel. Semua angka dihitung oleh **engine deterministik**, aturan OJK
tertanam di engine, dan LLM hanya **menarasikan** — tidak pernah menghitung.

- **Stack:** SvelteKit + FastAPI + PostgreSQL + Docker
- **Data per:** September 2026 (set asumsi `ID-2026-09`)
- **Catatan koreksi:** batas bunga pinjol mengikuti **SEOJK 19/SEOJK.06/2025** (mencabut SEOJK 19/2023):
  0,3%/hari untuk tenor ≤ 6 bulan dan 0,2%/hari untuk tenor > 6 bulan. Default "0,1%/hari" pada dokumen
  lama **tidak berlaku**.

## Fitur (P0)

| Kode | Fitur |
|---|---|
| F1 | Wizard 4 langkah (jenis penghasilan, tanggungan keluarga, keputusan, asumsi) |
| F2 | 3 template keputusan → twin A/B, C/D, E/F + Twin 0 baseline |
| F3 | Engine simulasi bulanan 240 bulan (bunga majemuk, inflasi, cicilan, denda, lock cap, macet >90 hari, nilai riil) |
| F4 | Regulatory Guard OJK (batas bunga/denda per tenor, DSR 30%, penanda SLIK) |
| F5 | Stress test 2 guncangan (kehilangan penghasilan 3 bulan, biaya darurat 2× di tahun ke-2) |
| F6 | Sensitivitas 3 preset + label "robust" / "bergantung asumsi" |
| F7 | Multiverse view (branch tree, net worth chart, time scrubber) |
| F8 | Compare (wealth gap + tabel selisih) |
| F9 | Narasi agent per horizon (LLM + fallback template, validator angka) |
| F10 | Rekomendasi deterministik + "Saya komit" (metrik dampak anonim) |
| F11 | Transparansi: panel asumsi bersumber, disclaimer di 3 lokasi |

## Mulai cepat

```bash
make init      # .env, build, up, migrate, seed
make health    # cek 5245 / 8072 / 5504
make seed-demo # persona Raka, Sinta, Dimas, Wulan + pre-cache narasi
```

Buka **http://localhost:5245**. API docs: **http://localhost:8072/docs**.

```
make up && make logs-be     # jalankan & lihat log
make test                   # unit test backend + frontend
make check                  # lint + typecheck + test
make e2e                    # Playwright (host)
make bench                  # benchmark engine (target < 300 ms)
make down                   # hentikan
```

## Arsitektur

```
Browser ──▶ SvelteKit (:5245) ──▶ FastAPI (:8072)
                                   ├─ Engine deterministik
                                   │   ├─ Regulatory Guard (OJK)
                                   │   ├─ Stress test
                                   │   └─ Sensitivitas 3 preset
                                   ├─ Scoring
                                   ├─ LLM Narrator + Validator ──fallback──▶ Template
                                   └─ PostgreSQL (:5504)
```

## Prinsip

1. **Angka dihitung engine, LLM hanya menarasikan.** Prompt hanya menerima `facts` terformat.
   Validator mengecek setiap angka di narasi ada di `facts`; kalau tidak → fallback template.
2. **Setiap asumsi punya sumber, tanggal, dan bisa diedit.** Set berversi (`ID-2026-09`),
   peringatan bila data > 6 bulan.
3. **Aturan OJK tertanam di engine.** Satu modul berversi (`regulatory.py`), dengan tanggal berlaku.

## Struktur

```
├── Makefile · docker-compose.yml · .env.example
├── docs/ (PRD.md, IMPLEMENTATION.md, ASSUMPTIONS.md, SOURCES.md)
├── backend/  → FastAPI + engine + LLM + Alembic + tests
└── frontend/ → SvelteKit 5 + Tailwind 4 + Vitest + Playwright
```

## Privasi

Tanpa akun, tanpa nama/NIK. Simulasi diidentifikasi UUID anonim, retensi 30 hari (UU 27/2022 PDP).

## Disclaimer

Financial Twin adalah alat simulasi edukatif, bukan nasihat keuangan, investasi, atau hukum.
Proyeksi bergantung pada asumsi dan tidak menjamin hasil. Konsultasikan keputusan penting dengan
perencana keuangan berlisensi.

## Verifikasi sebelum demo

- Batas bunga 0,3% / 0,2% diambil dari cuplikan resmi SEOJK 19/SEOJK.06/2025 dan ringkasan pihak
  ketiga yang konsisten. Beberapa sumber lama masih menyebut 0,1% (aturan 2023 yang sudah dicabut).
  **Verifikasi ulang ke PDF resmi di ojk.go.id.**
- Bunga penjaminan LPS 3,75% berlaku sampai 30 September 2026; periode baru perlu dicek.
- Return saham, premi upskilling, dan masa tunggu kerja **sengaja ditandai sebagai asumsi** di UI.
