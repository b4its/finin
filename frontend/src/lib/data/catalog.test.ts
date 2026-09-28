import { describe, it, expect } from 'vitest';
import { buildCatalog, metaFor, fieldTypeLabel, CATEGORY_LABELS, CATALOG_META } from './catalog';
import type { DecisionTemplate } from '$lib/api/types';

function makeTemplate(over: Partial<DecisionTemplate> = {}): DecisionTemplate {
	return {
		type: 'loan_vs_save',
		title: 'Pinjol/Paylater vs Nabung Dulu',
		twin_a: {
			code: 'A',
			label: 'Si Cicilan',
			color: '#F97362',
			dash: 'dashed',
			icon: 'credit-card'
		},
		twin_b: { code: 'B', label: 'Si Penabung', color: '#34D399', dash: 'dotted', icon: 'piggy' },
		fields: [{ key: 'loan.amount', label: 'Nominal pinjaman', type: 'currency' }],
		...over
	};
}

describe('metaFor', () => {
	it('mengembalikan ikon & kategori untuk tipe yang dikenal', () => {
		const meta = metaFor('kpr_vs_rent');
		expect(meta.category).toBe('aset');
		expect(meta.icon).toBe('🏠');
	});

	it('memberi fallback aman untuk tipe tak dikenal', () => {
		const meta = metaFor('tidak_ada');
		expect(meta.icon).toBe('🧩');
		expect(meta.keywords).toEqual([]);
	});

	it('setiap kategori yang dipakai metadata punya label', () => {
		for (const meta of Object.values(CATALOG_META)) {
			expect(CATEGORY_LABELS[meta.category]).toBeTruthy();
		}
	});
});

describe('fieldTypeLabel', () => {
	it('menerjemahkan tipe field umum ke bahasa Indonesia', () => {
		expect(fieldTypeLabel('currency')).toBe('Rupiah');
		expect(fieldTypeLabel('percent_daily')).toBe('Persen/hari');
		expect(fieldTypeLabel('instrument')).toBe('Instrumen');
	});

	it('mengembalikan tipe asli bila tidak dikenal', () => {
		expect(fieldTypeLabel('aneh')).toBe('aneh');
	});
});

describe('buildCatalog', () => {
	const templates = [
		makeTemplate(),
		makeTemplate({
			type: 'kpr_vs_rent',
			title: 'Beli Rumah KPR vs Sewa & Investasi',
			fields: [{ key: 'kpr.property_price', label: 'Harga properti', type: 'currency' }]
		}),
		makeTemplate({
			type: 'haji_furoda_vs_reguler',
			title: 'Haji Furoda vs Haji Reguler',
			fields: [{ key: 'haji.financing_amount', label: 'Nominal pembiayaan', type: 'currency' }]
		})
	];

	it('mengurutkan berdasarkan judul', () => {
		const rows = buildCatalog(templates, '', 'semua');
		expect(rows.map((r) => r.template.type)).toEqual([
			'kpr_vs_rent',
			'haji_furoda_vs_reguler',
			'loan_vs_save'
		]);
	});

	it('menyaring berdasarkan kategori', () => {
		const rows = buildCatalog(templates, '', 'aset');
		expect(rows.map((r) => r.template.type)).toEqual(['kpr_vs_rent']);
	});

	it('menyaring berdasarkan kata kunci judul', () => {
		const rows = buildCatalog(templates, 'rumah', 'semua');
		expect(rows).toHaveLength(1);
		expect(rows[0].template.type).toBe('kpr_vs_rent');
	});

	it('menyaring berdasarkan kata kunci sinonim (keywords) dan label field', () => {
		expect(buildCatalog(templates, 'pinjol', 'semua')).toHaveLength(1);
		expect(buildCatalog(templates, 'nominal pembiayaan', 'semua')).toHaveLength(1);
	});

	it('mengembalikan kosong saat tidak ada yang cocok', () => {
		expect(buildCatalog(templates, 'zzz-tidak-ada', 'semua')).toHaveLength(0);
	});

	it('menyertakan ikon & kategori pada tiap baris', () => {
		const rows = buildCatalog(templates, '', 'semua');
		expect(rows.every((r) => Boolean(r.icon) && Boolean(r.category))).toBe(true);
	});
});
