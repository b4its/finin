# Sumber Data — Financial Twin

Semua parameter default di `backend/app/data/assumptions/ID-2026-09.json` punya entri di sini.
Tanggal di bawah adalah tanggal rujukan data (*as of*), bukan tanggal publikasi.

## Regulasi

| Kode | Judul | Tanggal berlaku | URL |
|---|---|---|---|
| SEOJK 19/SEOJK.06/2025 | Penyelenggaraan Layanan Pendanaan Bersama Berbasis Teknologi Informasi — mencabut SEOJK 19/2023 | 31 Juli 2025 | https://www.ojk.go.id/id/regulasi/ |
| PMK 31/2024 | Sasaran inflasi 2,5 ± 1% untuk 2026–2027 | 2024 | https://www.kemenkeu.go.id/ |
| UU 27/2022 | Pelindungan Data Pribadi | 17 Oktober 2022 | https://peraturan.bpk.go.id/ |

Batas yang dipakai engine (SEOJK 19/SEOJK.06/2025):

- Bunga pinjol konsumtif: **0,3%/hari** untuk tenor ≤ 6 bulan, **0,2%/hari** untuk tenor > 6 bulan.
- Denda: **sama dengan batas bunga**.
- *Lock cap*: total bunga + denda ≤ **100% pokok**.
- Rasio cicilan: ≤ **30% penghasilan**, berlaku sejak 2026.
- Macet (TWP90): tunggakan **> 90 hari**.

## Makro (per September 2026)

| Parameter | Nilai | Sumber |
|---|---|---|
| BI-Rate | 5,75% (RDG 23 Sep 2026) | Bank Indonesia |
| Inflasi realisasi | 3,19% (Agustus 2026) | BPS |
| Bunga penjaminan LPS (bank umum) | 3,75% (s.d. 30 Sep 2026) | LPS |
| SR025 T3 / T5 | 6,80% / 6,90% | Kemenkeu (DJPPR) |
| Reksa dana pasar uang | 4–5,5%/th | Kompas.id |

## Survei & Riset

| Data | Nilai | Sumber |
|---|---|---|
| Indeks literasi keuangan | 69,57% | SNLIK 2026 |
| Indeks inklusi keuangan | 93,61% | SNLIK 2026 |
| Utang pinjol | Rp105,63 T (+24,76% yoy) | OJK, Juli 2026 |
| TWP90 pinjol | 4,32% | OJK, Juli 2026 |
| Kredit macet usia 19–34 | 48,65% | OJK, Maret 2026 |
| Paylater bank / pembiayaan | Rp31,5 T / Rp13,62 T | OJK, Mei–Juli 2026 |
| Pekerja menanggung 2 generasi | 90% | Sun Life Indonesia, Feb 2026 |
| Sandwich tanpa dana darurat | 52,2% | Katadata Insight Center, 2021 |
| Denda kartel bunga pinjol | Rp755 miliar (97 perusahaan) | KPPU, 26 Maret 2026 |
| Upah Sakernas Februari 2026 | SMA 3,08 jt; D1–D3 4,04 jt; D4–S3 4,77 jt | BPS |
| Imbal hasil pendidikan | ±4,7%/th sekolah | Purnastuti (2015) |
| Future self-continuity | $172 vs $80 alokasi pensiun | Hershfield dkk. (2011), JMR |
| Hyperbolic discounting | — | Laibson (1997) |

## Asumsi Tanpa Data Resmi (ditandai di UI)

Parameter berikut **sengaja ditandai sebagai asumsi** karena tidak ada data resmi yang langsung bisa dipakai:

- Premi upskilling (+10% setelah 12 bulan).
- Masa tunggu kerja lulusan (3 bulan).
- Imbal hasil reksa dana indeks saham jangka panjang (9%/th, volatilitas tinggi).
- Bunga tabungan bank reguler (1,0%/th).

## Catatan Verifikasi Sebelum Demo

- **Batas bunga pinjol.** Angka 0,3% / 0,2% diambil dari cuplikan dokumen resmi SEOJK 19/SEOJK.06/2025 dan ringkasan pihak ketiga yang konsisten. Beberapa sumber lama (termasuk satu halaman Kejaksaan) masih menyebut 0,1% sesuai aturan 2023 yang sudah dicabut. Verifikasi ulang ke PDF resmi di ojk.go.id.
- **Bunga penjaminan LPS 3,75%** hanya berlaku sampai 30 September 2026; periode baru perlu dicek.
- **Return saham, premi upskilling, masa tunggu kerja** adalah asumsi, bukan data resmi.
