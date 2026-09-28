/**
 * Metadata presentasi untuk katalog template keputusan.
 *
 * Backend (`GET /templates`) adalah sumber kebenaran untuk daftar template, persona
 * kembar, dan field masukan. File ini hanya menambahkan lapisan tampilan (ikon,
 * kategori, kata kunci pencarian) yang tidak dikirim API, sehingga katalog tetap
 * terdeskripsi tanpa menggandakan daftar template itu sendiri.
 */

import type { DecisionTemplate } from '$lib/api/types';

export type CatalogCategory = 'pinjaman' | 'keluarga' | 'karier' | 'aset' | 'proteksi';

export const CATEGORY_LABELS: Record<CatalogCategory, string> = {
	pinjaman: 'Pinjaman & Utang',
	keluarga: 'Keluarga & Gaya Hidup',
	karier: 'Karier & Pendidikan',
	aset: 'Aset & Investasi',
	proteksi: 'Proteksi & Kesehatan'
};

interface CatalogMeta {
	icon: string;
	category: CatalogCategory;
	blurb: string;
	keywords: string[];
}

/** Ikon + kategori per `type`. Kunci harus cocok dengan template backend. */
export const CATALOG_META: Record<string, CatalogMeta> = {
	loan_vs_save: {
		icon: '💳',
		category: 'pinjaman',
		blurb: 'Bandingkan beban cicilan pinjol/paylater versus menyicil ke tabungan sendiri.',
		keywords: ['pinjol', 'paylater', 'utang', 'bunga', 'cicilan']
	},
	study_vs_work: {
		icon: '🎓',
		category: 'karier',
		blurb: 'Lanjut S2 sekarang atau kerja dulu sambil upskilling dan menabung.',
		keywords: ['s2', 'kuliah', 'sekolah', 'upskill', 'gaji']
	},
	emergency_vs_invest: {
		icon: '🛡️',
		category: 'proteksi',
		blurb: 'Bangun dana darurat lebih dulu atau langsung agresif berinvestasi.',
		keywords: ['dana darurat', 'emergency', 'investasi', 'likuid']
	},
	kpr_vs_rent: {
		icon: '🏠',
		category: 'aset',
		blurb: 'Beli rumah dengan KPR atau tetap sewa sambil menginvestasikan selisihnya.',
		keywords: ['rumah', 'kpr', 'sewa', 'properti', 'cicilan']
	},
	vehicle_lease_vs_cash: {
		icon: '🚗',
		category: 'aset',
		blurb: 'Kredit mobil baru atau beli kendaraan bekas secara tunai.',
		keywords: ['mobil', 'motor', 'kredit', 'leasing', 'bekas']
	},
	wedding_grand_vs_intimate: {
		icon: '💍',
		category: 'keluarga',
		blurb: 'Pesta pernikahan mewah atau akad intim dengan modal awal untuk keluarga.',
		keywords: ['nikah', 'pernikahan', 'resepsi', 'wedding', 'modal']
	},
	franchise_vs_passive_invest: {
		icon: '🏪',
		category: 'karier',
		blurb: 'Buka franchise mikro dengan KUR atau investasi dividen pasif.',
		keywords: ['franchise', 'waralaba', 'kur', 'usaha', 'dividen']
	},
	child_education_unitlink_vs_diy: {
		icon: '🎒',
		category: 'keluarga',
		blurb: 'Dana pendidikan anak lewat unit link atau tabungan mandiri yang fleksibel.',
		keywords: ['anak', 'pendidikan', 'unit link', 'sekolah', 'tabungan']
	},
	haji_furoda_vs_reguler: {
		icon: '🕋',
		category: 'keluarga',
		blurb: 'Haji furoda cepat atau haji reguler sambil menumbuhkan sukuk.',
		keywords: ['haji', 'furoda', 'reguler', 'ibadah', 'sukuk']
	},
	career_corporate_vs_freelance: {
		icon: '💼',
		category: 'karier',
		blurb: 'Tetap di jalur korporat atau beralih menjadi pekerja lepas.',
		keywords: ['karier', 'kerja', 'freelance', 'korporat', 'resign']
	},
	rental_property_vs_dividend: {
		icon: '🏬',
		category: 'aset',
		blurb: 'Investasi properti sewa (kos) atau saham dividen.',
		keywords: ['properti', 'kos', 'sewa', 'dividen', 'saham']
	},
	electric_vehicle_vs_ice: {
		icon: '⚡',
		category: 'aset',
		blurb: 'Kendaraan listrik (EV) hemat energi atau kendaraan bensin (ICE) yang matang.',
		keywords: ['ev', 'listrik', 'bensin', 'ice', 'kendaraan', 'subsidi']
	},
	health_bpjs_vs_private: {
		icon: '🩺',
		category: 'proteksi',
		blurb: 'Cukup dengan BPJS Kesehatan atau tambah asuransi swasta murni.',
		keywords: ['bpjs', 'asuransi', 'kesehatan', 'medis', 'premi']
	}
};

const FALLBACK: CatalogMeta = {
	icon: '🧩',
	category: 'karier',
	blurb: 'Template keputusan finansial.',
	keywords: []
};

/** Metadata tampilan template; selalu mengembalikan nilai (ada fallback aman). */
export function metaFor(type: string): CatalogMeta {
	return CATALOG_META[type] ?? FALLBACK;
}

/** Format field masukan template menjadi label ringkas untuk chip ringkasan. */
export function fieldTypeLabel(t: string): string {
	switch (t) {
		case 'currency':
			return 'Rupiah';
		case 'percent':
			return 'Persen';
		case 'percent_daily':
			return 'Persen/hari';
		case 'int':
			return 'Angka bulat';
		case 'float':
			return 'Desimal';
		case 'instrument':
			return 'Instrumen';
		case 'bool':
			return 'Ya/Tidak';
		default:
			return t;
	}
}

export interface CatalogRow {
	template: DecisionTemplate;
	icon: string;
	category: CatalogCategory;
	blurb: string;
}

/** Urutkan + saring template untuk tampilan katalog. */
export function buildCatalog(
	templates: DecisionTemplate[],
	query: string,
	category: CatalogCategory | 'semua'
): CatalogRow[] {
	const q = query.trim().toLowerCase();
	return templates
		.map((template) => {
			const meta = metaFor(template.type);
			return { template, icon: meta.icon, category: meta.category, blurb: meta.blurb, meta };
		})
		.filter((row) => {
			if (category !== 'semua' && row.category !== category) return false;
			if (!q) return true;
			const haystack = [
				row.template.title,
				row.template.twin_a.label,
				row.template.twin_b.label,
				row.blurb,
				...row.meta.keywords,
				...row.template.fields.map((f) => f.label)
			]
				.join(' ')
				.toLowerCase();
			return haystack.includes(q);
		})
		.map(({ template, icon, category: cat, blurb }) => ({ template, icon, category: cat, blurb }))
		.sort((a, b) => a.template.title.localeCompare(b.template.title, 'id'));
}
