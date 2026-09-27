import { test, expect } from '@playwright/test';

// E2E jalur utama: Landing -> Wizard -> Multiverse -> Stress -> Rekomendasi -> Commit.
// Prasyarat: backend (8072) + frontend (5245) jalan, `make seed` sudah dijalankan.

test('landing menampilkan dirimu di masa depan', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByRole('heading', { name: /dirimu/i })).toBeVisible();
	await expect(page.getByText(/Data per|Berdasarkan data OJK/i).first()).toBeVisible();
});

test('wizard 4 langkah sampai multiverse', async ({ page }) => {
	await page.goto('/start');
	await page.waitForLoadState('networkidle');

	// Pertanyaan kedekatan (opsional) -> lewati
	const skip = page.getByRole('button', { name: /Lewati saja/i });
	if (await skip.isVisible().catch(() => false)) {
		await skip.click();
	}

	// Langkah 1: penghasilan sudah ada default, lanjut
	await expect(page.getByText('Penghasilanmu')).toBeVisible();
	await page.getByRole('button', { name: /^Lanjut/i }).click();

	// Langkah 2: posisi
	await expect(page.getByText('Posisi keuanganmu')).toBeVisible();
	await page.getByRole('button', { name: /^Lanjut/i }).click();

	// Langkah 3: keputusan — pilih template pinjol
	await expect(page.getByText(/Pilih keputusan/i)).toBeVisible();
	await page.getByRole('button', { name: /Pinjol\/Paylater vs Nabung Dulu/i }).click();

	// Bendera OJK live (bunga default 0,3% tepat di batas -> "Sesuai batas")
	await expect(page.getByText(/Sesuai batas|Di atas batas OJK/).first()).toBeVisible({ timeout: 8000 });

	await page.getByRole('button', { name: /^Lanjut/i }).click();

	// Langkah 4: asumsi
	await expect(page.getByText(/Asumsi makro/i)).toBeVisible({ timeout: 8000 });
	await page.getByRole('button', { name: /Bangun multiverse/i }).click();

	// Dashboard
	await expect(page).toHaveURL(/\/sim\//, { timeout: 25000 });
	await expect(page.getByText(/Multiverse-mu/i)).toBeVisible({ timeout: 25000 });
	await expect(page.getByText(/Kamu Tanpa Perubahan/).first()).toBeVisible();

	// Scrubber
	await page.getByRole('button', { name: 'th 20' }).click();

	// Stress test
	await page.getByRole('button', { name: /Kehilangan penghasilan 3 bulan/i }).click();
	await expect(page.getByText(/Bertahan/).first()).toBeVisible();

	// Bandingkan
	await expect(page.getByText(/Bandingkan dua twin/i)).toBeVisible();

	// Rekomendasi
	await expect(page.getByText(/Langkah pertama hari ini/i)).toBeVisible({ timeout: 20000 });
	const commit = page.getByRole('button', { name: /Saya komit langkah ini/i });
	await expect(commit).toBeVisible();
	await commit.click();
	await expect(page.getByRole('button', { name: /Terkomit/i })).toBeVisible();

	// Panel asumsi
	await page.getByRole('button', { name: /Asumsi & sumber/i }).click();
	await expect(page.getByText(/SEOJK-19-2025|Regulasi OJK/i).first()).toBeVisible();
});

test('bunga di atas batas memunculkan bendera merah', async ({ page }) => {
	await page.goto('/start');
	await page.getByRole('button', { name: /Lewati saja/i }).click();
	await page.getByRole('button', { name: /Lanjut/i }).click();
	await page.getByRole('button', { name: /Lanjut/i }).click();
	await page.getByRole('button', { name: /Pinjol\/Paylater vs Nabung Dulu/i }).click();

	// ubah bunga ke 0,6%/hari (di atas batas) — target input di sebelah label "Bunga per hari"
	const rateInput = page
		.locator('label', { hasText: 'Bunga per hari' })
		.locator('input[type="number"]');
	await rateInput.fill('0.6');

	await expect(page.getByText(/Di atas batas OJK/i).first()).toBeVisible({ timeout: 8000 });
	await expect(page.getByText(/indikasi pinjol ilegal/i).first()).toBeVisible();
});
