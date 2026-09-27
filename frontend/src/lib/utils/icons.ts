/** Peta nama ikon twin -> glif unicode.

Dipakai agar twin dibedakan dengan **warna + ikon + pola garis** (PRD §11),
bukan hanya warna — penting untuk pengguna dengan buta warna.
*/

const ICONS: Record<string, string> = {
	'circle-dashed': '◌', // baseline "Kamu Tanpa Perubahan"
	'credit-card': '▤', // Si Cicilan (pinjol/paylater)
	'piggy-bank': '◉', // Si Penabung
	'graduation-cap': '⬢', // Si Akademisi (S2)
	briefcase: '◆', // Si Praktisi (kerja + upskilling)
	shield: '⬟', // Si Siaga (dana darurat)
	'trending-up': '▲', // Si Agresif (investasi)
	home: '⌂', // KPR
	key: '⚿', // Sewa
	car: '🚘', // Si Pengkredit Leasing
	bike: '🏍', // Si Pembeli Bekas
	party: '🎉', // Si Pesta Akbar
	gem: '💎', // Si Intim & Modal Keluarga
	store: '🏪', // Si Pebisnis Waralaba
	'shield-alert': '🛡️', // Si Unit Link Pendidikan
	kaaba: '🕋', // Si Haji Khusus / Furoda
	moon: '🌙', // Si Haji Reguler & Sukuk Syariah
	circle: '●'
};

export function twinIcon(name: string): string {
	return ICONS[name] ?? ICONS.circle;
}

/** Label aksesibilitas untuk ikon (aria). */
export function twinIconLabel(name: string): string {
	const labels: Record<string, string> = {
		'circle-dashed': 'baseline tanpa perubahan',
		'credit-card': 'pinjaman',
		'piggy-bank': 'menabung',
		'graduation-cap': 'studi',
		briefcase: 'kerja',
		shield: 'dana darurat',
		'trending-up': 'investasi',
		home: 'rumah',
		key: 'sewa',
		car: 'kredit kendaraan leasing',
		bike: 'beli kendaraan bekas tunai',
		party: 'pesta resepsi pernikahan akbar',
		gem: 'nikah intim dan modal keluarga',
		store: 'usaha waralaba franchise',
		'shield-alert': 'asuransi proteksi unitlink',
		kaaba: 'haji furoda khusus',
		moon: 'haji reguler dan investasi syariah'
	};
	return labels[name] ?? 'twin';
}
