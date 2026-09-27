import { describe, it, expect } from 'vitest';
import { rupiah, rupiahBrief, percent, months, isStale } from './format';

describe('format', () => {
	it('rupiah', () => {
		expect(rupiah(12400000)).toBe('Rp12.400.000');
		expect(rupiah(0)).toBe('Rp0');
	});
	it('rupiahBrief', () => {
		expect(rupiahBrief(12400000)).toBe('Rp12,4 jt');
		expect(rupiahBrief(1200000000)).toBe('Rp1,2 M');
		expect(rupiahBrief(350000)).toBe('Rp350 rb');
	});
	it('percent', () => {
		expect(percent(0.15)).toBe('15,0%');
		expect(percent(0.3, 0)).toBe('30%');
	});
	it('months', () => {
		expect(months(6)).toBe('6,0 bulan');
	});
	it('isStale', () => {
		expect(isStale('2026-09-30')).toBe(false);
		expect(isStale('2020-01-01')).toBe(true);
	});
});
