# ASSUMPTIONS — Set `ID-2026-09`

Set asumsi ini adalah *source of truth* untuk engine. Semua nilai di sini juga tersedia
dalam bentuk machine-readable di `backend/app/data/assumptions/ID-2026-09.json`.

Konvensi:

- Semua tingkat (`rate`) dinyatakan **per tahun** sebagai desimal (0,03 = 3%), kecuali
  parameter pinjol yang eksplisit ditandai `/hari`.
- `null` berarti pengguna wajib mengisi sendiri (tidak ada default).
- Setiap parameter punya `source` (label + URL) dan `as_of` (tanggal rujukan).

## Preset

| Parameter (key) | Konservatif | Moderat | Optimis | Sumber |
|---|---|---|---|---|
| `inflation` | 0,040 | 0,030 | 0,025 | Sasaran BI 2,5±1%; realisasi Ags 2026 3,19% (BPS) |
| `returns.savings` | 0,010 | 0,010 | 0,010 | Asumsi (di bawah LPS) |
| `returns.deposit` | 0,030 | 0,035 | 0,040 | Di bawah LPS 3,75% agar terjamin |
| `returns.money_market` | 0,035 | 0,045 | 0,055 | Reksa dana pasar uang 4–5,5% (Kompas.id) |
| `returns.bond` | 0,060 | 0,068 | 0,070 | SR025 T3 6,80% / T5 6,90% (Kemenkeu) |
| `returns.stock` | 0,050 | 0,090 | 0,120 | Asumsi jangka panjang, berisiko |
| `salary_growth` | 0,030 | 0,050 | 0,070 | Asumsi; ref UMP 2026 5–7% |
| `s2_salary_premium` | 0,080 | 0,150 | 0,250 | Purnastuti 2015 (±4,7%) s.d. 6–11% |

## Parameter Non-Preset (sama di semua preset)

| Parameter | Nilai | Sumber |
|---|---|---|
| `bi_rate` | 0,0575 | BI RDG 23 Sep 2026 |
| `education_wage.sma` | 3.080.000 | Sakernas BPS Feb 2026 |
| `education_wage.d1_d3` | 4.040.000 | Sakernas BPS Feb 2026 |
| `education_wage.d4_s3` | 4.770.000 | Sakernas BPS Feb 2026 |
| `upskill_premium` | 0,10 (setelah 12 bulan) | Asumsi tanpa data resmi |
| `job_wait_months` | 3 | Asumsi |
| `emergency_fund_months_min` | 3 | Media Keuangan Kemenkeu |
| `emergency_fund_months_max` | 6 | Media Keuangan Kemenkeu |
| `s2_premium_range` | [0,08, 0,25] | Rentang edit yang diizinkan |

## Regulasi (SEOJK 19/SEOJK.06/2025)

| Parameter | Nilai |
|---|---|
| `consumer_caps` (tenor ≤ 6 bln) | bunga 0,003/hari, denda 0,003/hari |
| `consumer_caps` (tenor > 6 bln) | bunga 0,002/hari, denda 0,002/hari |
| `lock_cap_ratio` | 1,00 |
| `dsr_cap` | 0,30 |
| `default_days` | 90 |
