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

test('wizard 4 langkah sampai multiverse', async ({ page }) => {
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

test('halaman riwayat dapat dicari dan difilter', async ({ page }) => {
	// Buat satu simulasi agar riwayat terisi (store localStorage per konteks browser).
	await page.goto('/start');
	await page.waitForLoadState('networkidle');
	await skipFutureSelfQuestion(page);
	await page.getByRole('button', { name: /^Lanjut/i }).click();
	await page.getByRole('button', { name: /^Lanjut/i }).click();
	await page.getByRole('button', { name: /Pinjol\/Paylater vs Nabung Dulu/i }).first().click();
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
