# PRD — Financial Twin

**Versi:** 2.0 (MVP Hackathon, berbasis data) · **Stack:** SvelteKit + FastAPI + PostgreSQL + Docker · **Data per:** September 2026

## 1. Ringkasan Produk

Financial Twin adalah *decision-support system* yang membuat "kembaran digital" finansial pengguna di 3–4 skenario masa depan paralel pada horizon 5, 10, dan 20 tahun. Hasilnya divisualisasikan sebagai *multiverse* bercabang dan disimpulkan menjadi satu langkah pertama yang konkret.

Tiga prinsip utama:

1. **Angka dihitung oleh engine deterministik, sedangkan LLM hanya menarasikan.**
2. **Setiap asumsi punya sumber, tanggal, dan bisa diedit.**
3. **Aturan OJK tertanam di engine** (batas bunga, *lock cap*, batas rasio cicilan).

## 2. Masalah (Berbasis Data)

| Masalah | Data | Sumber |
|---|---|---|
| Akses mendahului pemahaman | Inklusi 93,61% vs literasi 69,57% | SNLIK 2026 (OJK–BPS–LPS) |
| Utang digital tumbuh cepat | Pinjol Rp105,63 T (+24,76% yoy), TWP90 4,32% | OJK, Juli 2026 |
| Anak muda paling rentan | 48,65% kredit macet pinjol dari usia 19–34 | OJK, Maret 2026 |
| Paylater untuk konsumsi | Bank Rp31,5 T (+31,22%), perusahaan pembiayaan Rp13,62 T (+54,65%); 93% konsumsi | OJK, Mei–Juli 2026 |
| Beban generasi sandwich | 90% pekerja menanggung dua generasi | Sun Life Indonesia, Februari 2026 |
| Tidak ada bantalan keuangan | 52,2% generasi sandwich belum punya dana darurat | Katadata Insight Center, 2021 |
| Praktik harga tidak sehat | KPPU mendenda 97 perusahaan pinjol Rp755 miliar atas kartel bunga | KPPU, 26 Maret 2026 |

**Akar masalah:** *present bias*. Manusia menilai imbalan hari ini jauh lebih tinggi daripada konsekuensi di masa depan. Aplikasi budgeting hanya mencatat masa lalu, kalkulator hanya menghitung satu skenario, dan belum ada alat yang membuat "diri di masa depan" terasa nyata.

## 3. Landasan Ilmiah

- **Future self-continuity** (Hershfield dkk., 2011, *Journal of Marketing Research*): interaksi dengan representasi visual diri masa depan meningkatkan alokasi tabungan lebih dari 2 kali lipat ($172 vs $80). Ini yang membenarkan konsep "twin".
- **Hyperbolic discounting** (Laibson, 1997): menjelaskan kenapa pinjol dan paylater terasa murah hari ini.
- **Opportunity cost & ceteris paribus:** setiap twin hanya mengubah **satu** variabel keputusan, sisanya sama dengan baseline, supaya perbandingannya adil.
- **Scenario planning & sensitivity analysis:** rekomendasi diuji dengan 3 preset asumsi. Kalau pemenangnya selalu sama, hasilnya diberi label "robust".

## 4. Persona

| Persona | Kondisi | Keputusan |
|---|---|---|
| Raka, 20, mahasiswa | Uang saku Rp2,5 jt, tabungan Rp3 jt | Pinjol/paylater Rp2 jt untuk HP vs menabung dulu |
| Sinta, 23, fresh graduate | Gaji Rp6 jt, tabungan Rp10 jt | S2 sekarang vs kerja + upskilling |
| Dimas, 28, generasi sandwich | Gaji Rp8 jt, kirim orang tua Rp1,5 jt/bulan | Dana darurat dulu vs langsung investasi |
| Wulan, 26, freelancer/ojol | Penghasilan tidak tetap Rp4–7 jt | Seberapa besar bantalan yang aman? (stress test) |
| Juri | 5–10 menit | Butuh "aha moment" visual dalam 60 detik |

## 5. Tujuan & Metrik

| Tujuan | Metrik | Target MVP |
|---|---|---|
| Cepat dipahami | Waktu dari landing sampai multiverse tampil | < 90 detik |
| Kredibel | Parameter yang punya sumber + tanggal | 100% |
| Performa | Engine 4 twin × 240 bulan × 3 preset | < 300 ms |
| Narasi akurat | Angka di narasi cocok dengan engine | 100% (validator) |
| Dampak perilaku | Skor *future self-continuity* sebelum vs sesudah (skala lingkaran 1–7) | Naik ≥ 1 poin rata-rata saat uji pengguna |
| Aksi nyata | Pengguna yang menekan "Saya komit langkah ini" | ≥ 40% saat uji pengguna |
| Andal saat demo | Tetap jalan tanpa LLM | Ya |

## 6. Ruang Lingkup

**P0 (MVP):** wizard 4 langkah (termasuk tanggungan keluarga dan jenis penghasilan), 3 template keputusan, engine bulanan 20 tahun, Regulatory Guard OJK, stress test 2 guncangan, sensitivitas 3 preset, multiverse view, scrubber, compare, narasi LLM + fallback, rekomendasi, panel asumsi bersumber, disclaimer, link hasil.

**P1:** template KPR vs sewa, Monte Carlo (p10/p50/p90), ekspor PDF, mode presentasi.

**Out-of-scope:** akun/login, integrasi rekening bank, rekomendasi produk atau merek tertentu, pajak rinci, aplikasi native.

## 7. Fitur

**F1 — Wizard Input (4 langkah)**

1. **Penghasilan:** nominal, jenis (gaji tetap / uang saku / tidak tetap + rentang min–maks), dan pengeluaran rata-rata.
2. **Posisi:** usia, tabungan, utang berjalan (sisa pokok + cicilan), dan **tanggungan keluarga per bulan**.
3. **Keputusan:** pilih 1–2 template (F2).
4. **Asumsi:** pilih preset (Konservatif / Moderat / Optimis) atau edit manual.

Validasi: nominal ≥ 0, usia 15–60, peringatan jika defisit, dan peringatan jika cicilan berjalan > 30% penghasilan.

**F2 — Template Keputusan (P0)**

| Template | Twin | Parameter kunci |
|---|---|---|
| Pinjol/Paylater vs Nabung Dulu | A "Si Cicilan" / B "Si Penabung" | Nominal, tenor, bunga/hari atau bulan, instrumen tabungan |
| S2 vs Kerja + Upskilling | C "Si Akademisi" / D "Si Praktisi" | Durasi, biaya total, kuliah sambil kerja (ya/tidak), premi gaji, biaya kursus |
| Dana Darurat Dulu vs Langsung Investasi | E "Si Siaga" / F "Si Agresif" | Target dana darurat (3–6 bulan), porsi investasi |

Aturan: 1 keputusan menghasilkan 2 twin + **Twin 0 "Kamu Tanpa Perubahan"** sebagai baseline. 2 keputusan menghasilkan 4 twin. Maksimal 4 twin tampil.

**F3 — Engine Simulasi.** Simulasi bulanan sampai 240 bulan yang mencakup: bunga majemuk, inflasi, pertumbuhan penghasilan per jalur, cicilan (anuitas / bunga harian flat), denda, *lock cap*, status macet (> 90 hari), tanggungan keluarga yang ikut naik dengan inflasi, dana darurat, net worth nominal dan riil.

**F4 — Regulatory Guard (OJK).** Pemeriksaan otomatis untuk template pinjol:

- Bunga/denda melebihi batas SEOJK 19/SEOJK.06/2025 memunculkan bendera merah "Di atas batas OJK, kemungkinan pinjol ilegal. Cek status di situs resmi OJK."
- Rasio cicilan > 30% penghasilan memunculkan bendera oranye "Melebihi batas kemampuan bayar yang dipakai OJK."
- Kalau twin macet, muncul penanda "Tercatat di SLIK OJK; akses kredit formal (misalnya KPR) bisa terhambat."

**F5 — Stress Test "Bagaimana Jika?"** Ada dua guncangan satu klik: (a) kehilangan penghasilan 3 bulan, (b) biaya darurat sebesar 2 kali pengeluaran bulanan di tahun ke-2. Sistem menunjukkan twin mana yang bertahan tanpa berutang baru.

**F6 — Sensitivitas & Label Robust.** Setiap twin dihitung dengan 3 preset. Kalau pemenangnya sama di ketiganya, tampil label "Rekomendasi robust". Kalau tidak, tampil "Bergantung asumsi" beserta parameter pemicunya.

**F7 — Multiverse Visualization.** Diagram bercabang "Kamu Hari Ini" ke tiap twin dengan node di tahun 5/10/20, grafik net worth, scrubber waktu, dan tooltip berisi aset, utang, arus kas, serta bendera.

**F8 — Compare.** Pilih 2 twin untuk melihat grafik area *wealth gap* per tahun dan tabel selisih metrik.

**F9 — Narasi Agent.** Narasi per horizon yang hanya memakai angka dari engine, misalnya: *"Tahun ke-5: Twin A masih menanggung sisa cicilan Rp1,2 jt, sementara Twin B sudah punya dana darurat 6 bulan."*

**F10 — Rekomendasi.** Skor deterministik menentukan twin terbaik. LLM lalu menjelaskan "Langkah pertama hari ini" beserta alasan komparatifnya. Pengguna bisa menekan tombol "Saya komit" (dicatat anonim untuk metrik dampak).

**F11 — Transparansi.** Panel asumsi menampilkan nilai, tanggal, dan tautan sumber. Disclaimer tampil di 3 lokasi.

## 8. Model Perhitungan

- Konversi bunga tahunan ke bulanan: `r_m = (1 + r_a)^(1/12) − 1`
- Anuitas: `P = L · i / (1 − (1+i)^−n)`
- Pinjol (flat harian): `total_manfaat = min(pokok × rate_harian × hari_tenor, 1,00 × pokok)`, `cicilan = (pokok + total_manfaat) / tenor`
- Denda: `denda_hari = baki × rate_denda`, dengan syarat kumulatif manfaat + denda ≤ 100% pokok
- Macet: tunggakan > 90 hari (definisi TWP90)
- Rasio cicilan (DSR): `total_cicilan / penghasilan`, bendera jika > 0,30
- Nilai riil: `V_riil = V_nom / (1 + inflasi)^(t/12)`
- Dana darurat (bulan): `kas_likuid / (pengeluaran + tanggungan)`
- Satu bulan = 365/12 ≈ 30,42 hari

**Skor rekomendasi (0–1):**

`0,30·NW_riil_th10(norm) + 0,25·min(dana_darurat_min/6, 1) + 0,20·(1 − min(DSR_rata/0,30, 1)) + 0,15·lolos_stress + 0,10·menang_di_preset/3`

Aturan keras: twin yang macet atau punya DSR > 30% selama lebih dari 6 bulan tidak boleh direkomendasikan, kecuali semua twin mengalaminya.

## 9. Basis Data & Sumber (Default Preset Moderat)

| Parameter | Default | Per | Sumber / dasar |
|---|---|---|---|
| Inflasi | 3,0%/th | Sep 2026 | Sasaran BI 2,5 ± 1% (PMK 31/2024); realisasi Agustus 2026 3,19% (BPS) |
| BI-Rate (konteks) | 5,75% | 23 Sep 2026 | RDG Bank Indonesia |
| Tabungan bank | 1,0%/th | — | Asumsi; tabungan reguler umumnya di bawah bunga penjaminan LPS |
| Deposito (dijamin LPS) | 3,5%/th | Jul–Sep 2026 | Di bawah bunga penjaminan LPS bank umum 3,75% agar tetap dijamin |
| Reksa dana pasar uang | 4,5%/th | 2026 | Imbal hasil bersih setahun di kisaran 4–5,5% (Kompas.id) |
| SBN ritel | 6,8%/th | Ags–Sep 2026 | SR025: T3 6,80%, T5 6,90% (Kemenkeu) |
| Reksa dana indeks saham | 9%/th, volatilitas tinggi | — | **Asumsi jangka panjang**, bukan jaminan; ditandai berisiko |
| Kenaikan gaji nominal | 5%/th | 2026 | Asumsi; referensi kenaikan UMP 2026 rata-rata 5–7% |
| Upah dasar per pendidikan | SMA 3,08 jt; D1–D3 4,04 jt; D4–S3 4,77 jt | Feb 2026 | Sakernas BPS (dipakai sebagai default jika pengguna tidak mengisi gaji) |
| Premi gaji S2 | +15% (rentang 8–25%) | — | Imbal hasil pendidikan Indonesia sekitar 4,7%/th (Purnastuti 2015) hingga 6–11%/th |
| Premi upskilling | +10% setelah 12 bulan | — | **Asumsi tanpa data resmi**; bisa diedit |
| Masa tunggu kerja lulusan | 3 bulan | — | Asumsi; bisa diedit |
| Batas bunga pinjol konsumtif | 0,3%/hari (tenor ≤ 6 bln); 0,2%/hari (> 6 bln) | Berlaku 2025– | SEOJK 19/SEOJK.06/2025 |
| Batas denda pinjol konsumtif | Sama dengan batas bunga | Berlaku 2025– | SEOJK 19/SEOJK.06/2025 |
| Lock cap | Bunga + denda ≤ 100% pokok | Berlaku 2025– | SEOJK 19/SEOJK.06/2025 |
| Batas rasio cicilan | 30% penghasilan | Sejak 2026 | SEOJK 19/SEOJK.06/2025 |
| Target dana darurat | 3–6 bulan biaya hidup | — | Media Keuangan Kemenkeu (untuk lajang) |
| Bunga paylater | Wajib diisi pengguna | — | Sangat bervariasi antar-penyedia, jadi tidak diberi default |

**Preset sensitivitas:**

| Parameter | Konservatif | Moderat | Optimis |
|---|---|---|---|
| Inflasi | 4,0% | 3,0% | 2,5% |
| Reksa dana pasar uang | 3,5% | 4,5% | 5,5% |
| SBN | 6,0% | 6,8% | 7,0% |
| Saham | 5% | 9% | 12% |
| Kenaikan gaji | 3% | 5% | 7% |
| Premi S2 | 8% | 15% | 25% |

## 10. Kebutuhan Non-Fungsional

- **Performa:** API < 500 ms p95 tanpa LLM; narasi di-stream lewat SSE.
- **Aksesibilitas:** WCAG AA; twin dibedakan dengan warna + ikon + pola garis; bisa dinavigasi dengan keyboard; ada tabel alternatif untuk grafik.
- **Responsif:** desktop-first, tetap layak di layar 375px.
- **Privasi (UU 27/2022 PDP):** tanpa akun, tanpa nama/NIK, UUID anonim, retensi 30 hari, minimisasi data.
- **Keandalan:** fallback template jika LLM gagal atau timeout > 8 detik.
- **Kesegaran data:** asumsi disimpan sebagai set berversi (`ID-2026-09`). UI menampilkan tanggal data, dan muncul peringatan jika data berumur > 6 bulan.

## 11. UX / UI

- **Metafora:** multiverse berlatar gelap bernuansa kosmik yang lembut, dengan angka berkontras tinggi.
- **Warna twin:** 0 `#94A3B8` abu-abu (baseline), A `#F97362` coral, B `#34D399` hijau, C `#818CF8` indigo, D `#FBBF24` amber. Pola garis: solid, putus-putus, titik, titik-garis.
- **Tipografi:** Inter untuk teks; tabular-nums untuk angka.
- **Prinsip:** *progressive disclosure* (default horizon 10 tahun), satu CTA utama per layar, angka ringkas ("Rp12,4 jt"), bahasa awam, bendera regulasi yang tidak menghakimi.
- **Alur layar:** Landing → (opsional) pertanyaan kedekatan dengan diri masa depan → Wizard → "Membangun multiverse..." → Dashboard → Drawer twin → Compare → Stress test → Rekomendasi → pertanyaan sesudah.
- **Teks disclaimer:** *"Financial Twin adalah alat simulasi edukatif, bukan nasihat keuangan, investasi, atau hukum. Proyeksi bergantung pada asumsi dan tidak menjamin hasil. Konsultasikan keputusan penting dengan perencana keuangan berlisensi."*

## 12. Risiko & Mitigasi

| Risiko | Mitigasi |
|---|---|
| Angka terkesan arbitrer | Sumber + tanggal di tiap parameter, 3 preset, label robust |
| Regulasi berubah | Aturan OJK disimpan di satu modul (`regulatory.py`) berversi, dengan tanggal berlaku |
| Isu hukum | Disclaimer, tanpa merek produk, tanpa ajakan membeli |
| LLM halusinasi angka | LLM hanya menerima fakta JSON, lalu validator angka; fallback template |
| Terkesan menghakimi pengguna pinjol | Bahasa netral ("konsekuensi", bukan "salah"); tetap menampilkan skenario pinjol dengan adil |
| UI kompleks | Maksimal 4 twin, satu slider, compare 2 twin |
| Demo offline | Persona seed + narasi pra-cache |

## 13. Milestone

| Minggu | Deliverable |
|---|---|
| 1 | Docker + Makefile, engine + regulatory + test, API, DB, seed asumsi |
| 2 | Wizard, multiverse, compare, stress test, sensitivitas, LLM |
| 3 | Rekomendasi, polish, E2E, seed persona, video demo |
