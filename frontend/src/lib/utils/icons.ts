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
		key: 'sewa'
	};
	return labels[name] ?? 'twin';
}
