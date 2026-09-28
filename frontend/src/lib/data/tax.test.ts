import { describe, it, expect } from 'vitest';
import { terRateFor, TER_A_TABLE, TER_B_TABLE, TER_C_TABLE } from './tax';

describe('terRateFor', () => {
	it('bebas pajak di bawah PTKP kategori A', () => {
		expect(terRateFor(5_000_000, 'A')).toBe(0);
	});

	it('menaikkan tarif bertahap untuk kategori A', () => {
		expect(terRateFor(6_000_000, 'A')).toBe(0.0075);
		expect(terRateFor(20_000_000, 'A')).toBe(0.09);
	});

	it('mencapai tarif tertinggi 34% pada penghasilan sangat tinggi', () => {
		expect(terRateFor(2_000_000_000, 'A')).toBe(0.34);
		expect(terRateFor(2_000_000_000, 'B')).toBe(0.34);
		expect(terRateFor(2_000_000_000, 'C')).toBe(0.34);
	});

	it('kategori berbeda punya batas berbeda', () => {
		// 5,5jt: A sudah kena 0,25% sementara B/C masih bebas (batas lebih tinggi).
		expect(terRateFor(5_500_000, 'A')).toBe(0.0025);
		expect(terRateFor(5_500_000, 'B')).toBe(0);
		expect(terRateFor(5_500_000, 'C')).toBe(0);
	});

	it('tabel monoton naik dan berakhir di 34%', () => {
		for (const table of [TER_A_TABLE, TER_B_TABLE, TER_C_TABLE]) {
			const last = table[table.length - 1];
			expect(last[0]).toBe(Infinity);
			expect(last[1]).toBe(0.34);
			for (let i = 1; i < table.length; i++) {
				expect(table[i][0]).toBeGreaterThan(table[i - 1][0]);
				expect(table[i][1]).toBeGreaterThanOrEqual(table[i - 1][1]);
			}
		}
	});
});
