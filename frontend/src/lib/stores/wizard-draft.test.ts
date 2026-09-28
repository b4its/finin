import { describe, it, expect, beforeEach, vi } from 'vitest';
import { saveDraft, loadDraft, clearDraft, DRAFT_KEY } from './wizard-draft';
import type { SimulationInput } from '$lib/api/client';

/** Stub localStorage minimal untuk environment node. */
const store = new Map<string, string>();
const localStorageStub = {
	getItem: (k: string) => (store.has(k) ? (store.get(k) as string) : null),
	setItem: (k: string, v: string) => void store.set(k, v),
	removeItem: (k: string) => void store.delete(k),
	clear: () => store.clear()
};

vi.stubGlobal('localStorage', localStorageStub);

function makeInput(over: Partial<SimulationInput> = {}): SimulationInput {
	return {
		profile: {
			age: 30,
			income_type: 'salary',
			income_monthly: 8_000_000,
			income_range: null,
			expense_monthly: 4_000_000,
			dependents_monthly: 0,
			savings: 10_000_000,
			existing_debt: { principal: 0, monthly_payment: 0, annual_rate: 0, tenor_months: 0 }
		},
		decisions: [{ type: 'loan_vs_save' } as never],
		preset: 'moderat',
		assumption_overrides: {},
		...over
	} as SimulationInput;
}

describe('wizard draft', () => {
	beforeEach(() => localStorageStub.clear());

	it('menyimpan dan memuat draf kembali', () => {
		const input = makeInput();
		saveDraft(input);
		const loaded = loadDraft(makeInput({ preset: 'konservatif' }));
		expect(loaded?.profile.income_monthly).toBe(8_000_000);
		expect(loaded?.preset).toBe('moderat');
		expect(loaded?.decisions).toHaveLength(1);
	});

	it('menggabungkan field default yang tidak ada di draf', () => {
		// Draf lama tanpa field tertentu tetap aman karena digabung dengan default.
		localStorageStub.setItem(
			DRAFT_KEY,
			JSON.stringify({
				profile: { age: 25, income_monthly: 5_000_000 },
				decisions: [],
				preset: 'optimis'
			})
		);
		const base = makeInput();
		const loaded = loadDraft(base);
		expect(loaded?.profile.expense_monthly).toBe(base.profile.expense_monthly);
		expect(loaded?.profile.age).toBe(25);
	});

	it('mengembalikan null bila tidak ada draf', () => {
		expect(loadDraft(makeInput())).toBeNull();
	});

	it('mengabaikan draf korup (bukan JSON)', () => {
		localStorageStub.setItem(DRAFT_KEY, '{bukan json');
		expect(loadDraft(makeInput())).toBeNull();
	});

	it('mengabaikan draf dengan bentuk tidak valid', () => {
		localStorageStub.setItem(DRAFT_KEY, JSON.stringify({ foo: 'bar' }));
		expect(loadDraft(makeInput())).toBeNull();
	});

	it('mengabaikan draf yang decisions-nya bukan array', () => {
		localStorageStub.setItem(
			DRAFT_KEY,
			JSON.stringify({ profile: { age: 30, income_monthly: 1 }, decisions: 'x', preset: 'moderat' })
		);
		expect(loadDraft(makeInput())).toBeNull();
	});

	it('menghapus draf', () => {
		saveDraft(makeInput());
		clearDraft();
		expect(loadDraft(makeInput())).toBeNull();
	});
});
