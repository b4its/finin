import { test, expect, type Page } from '@playwright/test';

// E2E jalur utama: Landing -> Wizard -> Multiverse -> Stress -> Rekomendasi -> Commit.
// Prasyarat: backend (8072) + frontend (5245) jalan, `make seed` sudah dijalankan.

/** Lewati pertanyaan kedekatan (opsional) bila muncul di langkah pertama. */
async function skipFutureSelfQuestion(page: Page) {
	const skip = page.getByRole('button', { name: /^Lewati$/ });
	if (await skip.isVisible().catch(() => false)) {
		await skip.click();
	}
}

test('landing menampilkan ajakan dan konteks pasar', async ({ page }) => {
	await page.goto('/');
	// Judul utama (h1) — gunakan level heading agar tidak bentrok dengan h3 "Dirimu".
	await expect(
		page.getByRole('heading', { level: 1, name: /Lihat dirimu di 5, 10, dan 20 tahun/i })
	).toBeVisible();
	await expect(page.getByText(/Berdasarkan data OJK/i).first()).toBeVisible();
	// Bagian "Cara kerjanya" baru.
	await expect(page.getByRole('heading', { name: /Cara kerjanya/i })).toBeVisible();
});

test('wizard 5 langkah sampai multiverse', async ({ page }) => {
	await page.goto('/start');
	await page.waitForLoadState('networkidle');
	await skipFutureSelfQuestion(page);

	// Langkah 1: penghasilan (default terisi) -> lanjut
	await expect(page.getByRole('heading', { name: 'Penghasilanmu' })).toBeVisible();
	await page.getByRole('button', { name: /^Lanjut/i }).click();

	// Langkah 2: posisi
	await expect(page.getByRole('heading', { name: 'Posisi keuanganmu' })).toBeVisible();
	await page.getByRole('button', { name: /^Lanjut/i }).click();

	// Langkah 3: keputusan — pilih template pinjol
	await expect(page.getByRole('heading', { name: /Pilih keputusan/i })).toBeVisible();
	await page.getByRole('button', { name: /Pinjol\/Paylater vs Nabung Dulu/i }).first().click();

	// Bendera OJK live (bunga default tepat di batas -> "Sesuai batas")
	await expect(page.getByText(/Sesuai batas|Di atas batas OJK/).first()).toBeVisible({
		timeout: 8000
	});

	await page.getByRole('button', { name: /^Lanjut/i }).click();

	// Langkah 4: asumsi
	await expect(page.getByRole('heading', { name: /Asumsi makro/i })).toBeVisible({ timeout: 8000 });
	await page.getByRole('button', { name: /^Lanjut/i }).click();

	// Langkah 5: ringkasan sebelum menjalankan simulasi
	await expect(page.getByRole('heading', { name: /Ringkasan sebelum membangun/i })).toBeVisible();
	await page.getByRole('button', { name: /Bangun multiverse/i }).click();

	// Dashboard
	await expect(page).toHaveURL(/\/sim\//, { timeout: 30000 });
	await expect(page.getByRole('heading', { level: 1, name: /Multiverse-mu/i })).toBeVisible({
		timeout: 30000
	});
	// Ringkasan eksekutif baru tampil lebih dulu.
	await expect(page.getByRole('heading', { name: /Ringkasan eksekutif/i })).toBeVisible();
	await expect(page.getByText(/Kamu Tanpa Perubahan/).first()).toBeVisible();

	// Scrubber tahun
	await page.getByRole('button', { name: 'th 20' }).click();

	// Buka tab Risiko lalu uji stress test
	await page.getByRole('tab', { name: /Risiko & Ketahanan/i }).click();
	await page.getByRole('button', { name: /Kehilangan penghasilan 3 bulan/i }).click();
	await expect(page.getByText(/Bertahan/).first()).toBeVisible();

	// Kembali ke tab overview untuk melihat CompareView
	await page.getByRole('tab', { name: /Multiverse Utama/i }).click();
	await expect(page.getByText(/Bandingkan selisih kekayaan head-to-head/i)).toBeVisible();

	// Rekomendasi
	await expect(page.getByText(/Langkah pertama hari ini/i)).toBeVisible({ timeout: 20000 });
	const commit = page.getByRole('button', { name: /Saya komit langkah ini/i });
	await expect(commit).toBeVisible();
	await commit.click();
	await expect(page.getByRole('button', { name: /Terkomit/i })).toBeVisible();

	// Panel asumsi
	await page.getByRole('button', { name: /Asumsi & sumber/i }).click();
	await expect(page.getByText(/Regulasi OJK/i).first()).toBeVisible();
});

test('bunga di atas batas memunculkan bendera merah', async ({ page }) => {
	await page.goto('/start');
	await page.waitForLoadState('networkidle');
	await skipFutureSelfQuestion(page);
	await page.getByRole('button', { name: /^Lanjut/i }).click();
	await page.getByRole('button', { name: /^Lanjut/i }).click();
	await page.getByRole('button', { name: /Pinjol\/Paylater vs Nabung Dulu/i }).first().click();

	// Naikkan bunga ke 0,6%/hari (di atas batas 0,3%).
	const rateInput = page
		.locator('label', { hasText: 'Bunga per hari' })
		.locator('input[type="number"]');
	await rateInput.fill('0.6');

	await expect(page.getByText(/Di atas batas OJK/i).first()).toBeVisible({ timeout: 8000 });
});

test('wizard memulihkan draf setelah reload dan bisa direset', async ({ page }) => {
	await page.goto('/start');
	await page.waitForLoadState('networkidle');
	await skipFutureSelfQuestion(page);

	// Ubah penghasilan lalu reload: nilai harus dipulihkan dari draf lokal.
	const income = page.locator('input[inputmode="numeric"]').first();
	await income.fill('9500000');
	await page.waitForTimeout(700); // menunggu debounce penulisan draf

	await page.reload();
	await page.waitForLoadState('networkidle');
	await expect(page.locator('input[inputmode="numeric"]').first()).toHaveValue('9.500.000');

	// "Mulai dari awal" mengharuskan konfirmasi, lalu mengembalikan ke default.
	await page.getByRole('button', { name: /^Lanjut/i }).click();
	await page.getByRole('button', { name: /Mulai dari awal/i }).click();
	await page.getByRole('button', { name: /Yakin\? Semua isian dihapus/i }).click();
	await expect(page.getByText(/Langkah 1 dari 5/i)).toBeVisible();
	await expect(page.locator('input[inputmode="numeric"]').first()).toHaveValue('6.000.000');
});

test('memilih persona non-variabel membersihkan rentang penghasilan lama', async ({ page }) => {
	await page.goto('/start');
	await page.waitForLoadState('networkidle');
	await skipFutureSelfQuestion(page);

	// Pilih Wulan (penghasilan variabel) -> rentang Wulan 4jt–7jt muncul.
	await page.getByRole('button', { name: /Wulan/ }).click();
	await expect(page.getByText(/Rentang penghasilan \(untuk stress test\)/)).toBeVisible();
	const minInput = page.locator('label', { hasText: 'Minimum' }).locator('input');
	await expect(minInput).toHaveValue('4.000.000');

	// Pilih Sinta (gaji tetap, tanpa rentang) -> rentang lama harus dibersihkan.
	await page.getByRole('button', { name: /Sinta/ }).click();

	// Kembalikan jenis penghasilan ke "Tidak tetap": rentang diisi ulang dari
	// penghasilan Sinta (6jt -> 4,2jt), bukan nilai Wulan yang tertinggal.
	await page.getByRole('button', { name: /Tidak tetap/i }).click();
	await expect(page.getByText(/Rentang penghasilan \(untuk stress test\)/)).toBeVisible();
	await expect(page.locator('label', { hasText: 'Minimum' }).locator('input')).toHaveValue('4.200.000');
});

test('halaman riwayat dapat dicari dan difilter', async ({ page }) => {
	// Buat satu simulasi agar riwayat terisi (store localStorage per konteks browser).
	await page.goto('/start');
	await page.waitForLoadState('networkidle');
	await skipFutureSelfQuestion(page);
	await page.getByRole('button', { name: /^Lanjut/i }).click();
	await page.getByRole('button', { name: /^Lanjut/i }).click();
	await page.getByRole('button', { name: /Pinjol\/Paylater vs Nabung Dulu/i }).first().click();
	await page.getByRole('button', { name: /^Lanjut/i }).click();
	await page.getByRole('button', { name: /^Lanjut/i }).click();
	await page.getByRole('button', { name: /Bangun multiverse/i }).click();
	await expect(page).toHaveURL(/\/sim\//, { timeout: 30000 });

	await page.goto('/saya');
	await expect(page.getByRole('heading', { level: 1, name: /Simulasi saya/i })).toBeVisible();
	// Kontrol pencarian & filter harus muncul karena riwayat sudah terisi.
	await expect(page.getByRole('searchbox', { name: /Cari riwayat/i })).toBeVisible();
	await expect(page.getByRole('combobox', { name: /Filter berdasarkan preset/i })).toBeVisible();

	// Pencarian yang tidak cocok menampilkan keadaan kosong, bukan error.
	await page.getByRole('searchbox', { name: /Cari riwayat/i }).fill('zzz-tidak-ada');
	await expect(page.getByText(/Tidak ada simulasi yang cocok/i)).toBeVisible();
});

test('perbandingan responsif dapat dibagikan melalui URL', async ({ page }) => {
	const ids = ['sim-alpha', 'sim-beta'];
	await page.addInitScript((simulationIds) => {
		localStorage.setItem(
			'ft_history_v1',
			JSON.stringify(
				simulationIds.map((id, index) => ({
					id,
					label: `Skenario ${index + 1}`,
					created_at: Date.now() - index * 1000,
					preset: index ? 'optimis' : 'moderat',
					twin_count: 3,
					best_twin: 'E',
					best_net_worth_y10: 500_000_000 - index * 50_000_000
				}))
			)
		);
	}, ids);

	await page.route('**/simulations/*', async (route) => {
		const id = route.request().url().split('/').at(-1) ?? ids[0];
		const index = ids.indexOf(id);
		await route.fulfill({
			json: {
				id,
				preset: index ? 'optimis' : 'moderat',
				best_twin: 'E',
				robust: true,
				robust_reason: 'Konsisten',
				twins: [
					{
						code: 'E',
						label: 'Si Siaga',
						color: index ? '#f472b6' : '#22d3ee',
						score: 0.9 - index * 0.05,
						summary: { avg_dsr: 0.2 + index * 0.05 },
						yearly_series: [
							{
								year: 10,
								net_worth: 600_000_000 - index * 50_000_000,
								net_worth_real: 500_000_000 - index * 50_000_000,
								emergency_months: 8 - index,
								dsr: 0.2 + index * 0.05
							}
						]
					}
				]
			}
		});
	});

	await page.setViewportSize({ width: 390, height: 844 });
	await page.goto('/bandingkan');
	await page.getByRole('button', { name: /Skenario 1/i }).click();
	await page.getByRole('button', { name: /Skenario 2/i }).click();

	await expect(page).toHaveURL(/ids=sim-alpha%2Csim-beta/);
	await expect(page.getByRole('region', { name: /Ringkasan perbandingan/i })).toBeVisible();
	await expect(page.getByRole('article')).toHaveCount(2);
	await expect(page.getByText(/Net worth riil tahun ke-10/i)).toBeVisible();
	await expect
		.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth))
		.toBe(true);

	// Ekspor tersedia begitu minimal ada 2 simulasi terbandingkan.
	await expect(page.getByRole('button', { name: /Unduh CSV/i })).toBeVisible();
	await expect(page.getByRole('button', { name: /Unduh JSON/i })).toBeVisible();
	await expect(page.getByRole('button', { name: /Salin tautan/i })).toBeVisible();
	const download = page.waitForEvent('download');
	await page.getByRole('button', { name: /Unduh CSV/i }).click();
	await expect((await download).suggestedFilename()).toMatch(/perbandingan-simulasi-.*\.csv/);

	await page.reload();
	await expect(page.getByText(/Pilih simulasi \(2\/3\)/i)).toBeVisible();

	// Penerima tautan tidak harus memiliki riwayat lokal milik pengirim.
	await page.evaluate(() => localStorage.removeItem('ft_history_v1'));
	await page.reload();
	await expect(page.getByRole('region', { name: /Ringkasan perbandingan/i })).toBeVisible();
	await expect(page.getByRole('article')).toHaveCount(2);
});

test('katalog keputusan menyaring dan membuka wizard dengan template terpilih', async ({ page }) => {
	await page.goto('/katalog');
	await expect(
		page.getByRole('heading', { level: 1, name: /Katalog keputusan finansial/i })
	).toBeVisible();

	// Semua 13 template dari backend tampil sebagai kartu.
	await expect(page.getByRole('article')).toHaveCount(13);

	// Pencarian menyaring; kata kunci "rumah" hanya menyisakan template KPR.
	await page.getByRole('searchbox', { name: /Cari template keputusan/i }).fill('rumah');
	await expect(page.getByRole('article')).toHaveCount(1);
	await expect(page.getByText(/Beli Rumah KPR vs Sewa/i)).toBeVisible();

	// Kosongkan pencarian lalu buka satu template ke wizard via tautan dalam.
	await page.getByRole('searchbox', { name: /Cari template keputusan/i }).fill('');
	await expect(page.getByRole('article')).toHaveCount(13);
	await page.getByRole('link', { name: /Coba di wizard/i }).first().click();

	await expect(page).toHaveURL(/\/start\?template=/);
	await expect(
		page.getByRole('heading', { name: /Pilih keputusan yang mau dibandingkan/i })
	).toBeVisible();
	// Template terpilih otomatis -> formulir detailnya muncul (ada tombol aktif).
	await expect(page.locator('button.active').first()).toBeVisible();
});
