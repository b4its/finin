import { describe, it, expect, beforeEach, vi } from 'vitest';

/**
 * Uji store riwayat lokal. `localStorage` tidak tersedia di environment node,
 * jadi kita sediakan stub minimal sebelum modul diimpor.
 */
const store = new Map<string, string>();
const localStorageStub = {
	getItem: (k: string) => (store.has(k) ? (store.get(k) as string) : null),
	setItem: (k: string, v: string) => store.set(k, v),
	removeItem: (k: string) => store.delete(k),
	clear: () => store.clear()
};

vi.stubGlobal('localStorage', localStorageStub);

const { history } = await import('./history.svelte');

describe('history store', () => {
	beforeEach(() => {
		store.clear();
		history.clear();
	});

	it('adds records with newest first and creates a timestamp', () => {
		history.add({
			id: 'a',
			twin_count: 5,
			best_twin: 'D',
			preset: 'moderat',
			label: 'Rp8 jt/bln'
		});
		history.add({
			id: 'b',
			twin_count: 3,
			best_twin: 'B',
			preset: 'optimis',
			label: 'Rp5 jt/bln'
		});
		expect(history.items.map((r) => r.id)).toEqual(['b', 'a']);
		expect(typeof history.items[0].created_at).toBe('number');
	});

	it('de-duplicates by id (re-adding moves to front)', () => {
		history.add({ id: 'a', twin_count: 5, best_twin: 'D', preset: 'moderat', label: 'x' });
		history.add({ id: 'b', twin_count: 5, best_twin: 'D', preset: 'moderat', label: 'y' });
		history.add({ id: 'a', twin_count: 6, best_twin: 'A', preset: 'moderat', label: 'x2' });
		expect(history.items.map((r) => r.id)).toEqual(['a', 'b']);
		expect(history.items[0].twin_count).toBe(6);
	});

	it('removes a record by id', () => {
		history.add({ id: 'a', twin_count: 5, best_twin: 'D', preset: 'moderat', label: 'x' });
		history.remove('a');
		expect(history.items).toHaveLength(0);
	});

	it('persists the optional net worth snapshot', () => {
		history.add({
			id: 'a',
			twin_count: 5,
			best_twin: 'D',
			preset: 'moderat',
			label: 'x',
			best_net_worth_y10: 841_000_000,
			income_monthly: 8_000_000
		});
		expect(history.items[0].best_net_worth_y10).toBe(841_000_000);
		expect(history.items[0].income_monthly).toBe(8_000_000);
	});

	it('tolerates corrupt payloads on load', () => {
		store.set('ft_history_v1', '{not json');
		history.load();
		expect(history.items).toEqual([]);
		store.set('ft_history_v1', JSON.stringify([{ id: 42 }, { id: 'ok' }]));
		history.load();
		expect(history.items.map((r) => r.id)).toEqual(['ok']);
	});
});
