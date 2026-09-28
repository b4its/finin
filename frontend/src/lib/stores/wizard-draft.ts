/**
 * Draf wizard yang disimpan lokal (localStorage).
 *
 * Tujuan: pengguna tidak kehilangan isian 5 langkah ketika memuat ulang halaman
 * atau menutup tab secara tidak sengaja. Menghormati prinsip privasi aplikasi —
 * data tetap di perangkat, tanpa akun, dan dihapus setelah simulasi dijalankan.
 *
 * Logika dipisah dari store agar mudah diuji tanpa runes Svelte.
 */

import type { SimulationInput } from '$lib/api/client';

export const DRAFT_KEY = 'ft_wizard_draft_v1';

/** Bentuk minimal yang cukup untuk memvalidasi draf tersimpan. */
function isPlausibleInput(v: unknown): v is SimulationInput {
	if (!v || typeof v !== 'object') return false;
	const o = v as Record<string, unknown>;
	const profile = o.profile as Record<string, unknown> | undefined;
	if (!profile || typeof profile !== 'object') return false;
	if (typeof profile.age !== 'number' || typeof profile.income_monthly !== 'number') return false;
	if (!Array.isArray(o.decisions)) return false;
	if (typeof o.preset !== 'string') return false;
	return true;
}

/** Simpan draf. Diam-diam gagal (mis. storage penuh / mode privat). */
export function saveDraft(input: SimulationInput): void {
	if (typeof localStorage === 'undefined') return;
	try {
		localStorage.setItem(DRAFT_KEY, JSON.stringify(input));
	} catch {
		/* abaikan */
	}
}

/** Muat draf bila ada dan berbentuk valid; jika tidak, kembalikan null. */
export function loadDraft(base: SimulationInput): SimulationInput | null {
	if (typeof localStorage === 'undefined') return null;
	try {
		const raw = localStorage.getItem(DRAFT_KEY);
		if (!raw) return null;
		const parsed = JSON.parse(raw);
		if (!isPlausibleInput(parsed)) return null;
		// Gabungkan dengan default agar field baru (masa depan) tetap terisi aman.
		return {
			...base,
			...parsed,
			profile: { ...base.profile, ...parsed.profile },
			assumption_overrides: parsed.assumption_overrides ?? {}
		};
	} catch {
		return null;
	}
}

export function clearDraft(): void {
	if (typeof localStorage === 'undefined') return;
	try {
		localStorage.removeItem(DRAFT_KEY);
	} catch {
		/* abaikan */
	}
}
