/** Utilitas format angka & tanggal (bahasa Indonesia). */

/** Rp12.400.000 */
export function rupiah(x: number): string {
	if (!isFinite(x)) return 'Rp0';
	const sign = x < 0 ? '-' : '';
	return sign + 'Rp' + Math.round(Math.abs(x)).toLocaleString('id-ID');
}

/** Rp12,4 jt / Rp1,2 M / Rp350 rb */
export function rupiahBrief(x: number): string {
	if (!isFinite(x)) return 'Rp0';
	const sign = x < 0 ? '-' : '';
	const ax = Math.abs(x);
	if (ax >= 1e12) return `${sign}Rp${(ax / 1e12).toFixed(1).replace('.', ',')} T`;
	if (ax >= 1e9) return `${sign}Rp${(ax / 1e9).toFixed(1).replace('.', ',')} M`;
	if (ax >= 1e6) return `${sign}Rp${(ax / 1e6).toFixed(1).replace('.', ',')} jt`;
	if (ax >= 1e3) return `${sign}Rp${(ax / 1e3).toFixed(0)} rb`;
	return `${sign}Rp${Math.round(ax).toLocaleString('id-ID')}`;
}

/** 12,4% */
export function percent(x: number, digits = 1): string {
	if (!isFinite(x)) return '—';
	return `${(x * 100).toFixed(digits).replace('.', ',')}%`;
}

/** 0,3%/hari */
export function percentDaily(x: number): string {
	return `${(x * 100).toFixed(2).replace('.', ',')}%/hari`;
}

/** 6,0 bulan */
export function months(x: number): string {
	return `${x.toFixed(1).replace('.', ',')} bulan`;
}

/** 30 Sep 2026 */
export function dateID(iso: string): string {
	try {
		const d = new Date(iso);
		return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
	} catch {
		return iso;
	}
}

/** Umur data dalam bulan (untuk peringatan > 6 bulan). */
export function ageInMonths(iso: string): number {
	const d = new Date(iso).getTime();
	const now = Date.now();
	return (now - d) / (1000 * 60 * 60 * 24 * 30.44);
}

export function isStale(iso: string, thresholdMonths = 6): boolean {
	return ageInMonths(iso) > thresholdMonths;
}

/** Terbilang sederhana untuk konteks demo. */
export function yearLabel(y: number): string {
	return `Tahun ke-${y}`;
}
