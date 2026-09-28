import { describe, it, expect } from 'vitest';
import {
	validateIncome,
	validatePosition,
	validateDecision,
	validateAssumption,
	validateStep
} from './wizard-validation';
import type { SimulationInput } from '$lib/api/client';

function makeInput(overrides: Partial<SimulationInput> = {}): SimulationInput {
	return {
		profile: {
			age: 23,
			income_type: 'salary',
			income_monthly: 6_000_000,
			income_range: null,
			expense_monthly: 3_800_000,
			dependents_monthly: 500_000,
			savings: 5_000_000,
			existing_debt: { principal: 0, monthly_payment: 0, annual_rate: 0, tenor_months: 0 }
		},
		decisions: [],
		preset: 'moderat',
		assumption_overrides: {},
		...overrides
	} as SimulationInput;
}

describe('validateIncome', () => {
	it('valid untuk gaji tetap dengan penghasilan > 0', () => {
		expect(validateIncome(makeInput()).valid).toBe(true);
	});

	it('invalid untuk gaji tetap tanpa penghasilan', () => {
		const input = makeInput();
		input.profile.income_monthly = 0;
		const res = validateIncome(input);
		expect(res.valid).toBe(false);
		expect(res.issues[0].field).toBe('income_monthly');
	});

	it('mengizinkan penghasilan 0 untuk tipe tidak tetap (variable)', () => {
		const input = makeInput();
		input.profile.income_type = 'variable';
		input.profile.income_monthly = 0;
		expect(validateIncome(input).valid).toBe(true);
	});

	it('tetap menolak penghasilan 0 untuk uang saku (allowance)', () => {
		// Uang saku juga penghasilan tetap/bulanan -> wajib > 0.
		const input = makeInput();
		input.profile.income_type = 'allowance';
		input.profile.income_monthly = 0;
		expect(validateIncome(input).valid).toBe(false);
	});

	it('invalid bila pengeluaran negatif', () => {
		const input = makeInput();
		input.profile.expense_monthly = -1;
		expect(validateIncome(input).valid).toBe(false);
	});

	it('memperingatkan defisit tanpa memblokir simulasi', () => {
		const input = makeInput();
		input.profile.expense_monthly = 7_000_000;
		const res = validateIncome(input);
		expect(res.valid).toBe(true);
		expect(res.issues).toEqual([
			expect.objectContaining({ field: 'expense_monthly', blocking: false })
		]);
	});

	it('menandai rentang penghasilan terbalik untuk tipe variable', () => {
		const input = makeInput();
		input.profile.income_type = 'variable';
		input.profile.income_range = { min: 9_000_000, max: 1_000_000 };
		const res = validateIncome(input);
		expect(res.issues.some((i) => i.field === 'income_range')).toBe(true);
	});
});

describe('validatePosition', () => {
	it('valid untuk usia wajar', () => {
		expect(validatePosition(makeInput()).valid).toBe(true);
	});

	it('invalid untuk usia di bawah 15', () => {
		const input = makeInput();
		input.profile.age = 10;
		const res = validatePosition(input);
		expect(res.valid).toBe(false);
		expect(res.issues[0].field).toBe('age');
	});

	it('invalid untuk usia di atas 60', () => {
		const input = makeInput();
		input.profile.age = 70;
		expect(validatePosition(input).valid).toBe(false);
	});

	it('invalid untuk tabungan negatif', () => {
		const input = makeInput();
		input.profile.savings = -1;
		expect(validatePosition(input).valid).toBe(false);
	});

	it('invalid untuk cicilan berjalan negatif', () => {
		const input = makeInput();
		input.profile.existing_debt.monthly_payment = -100;
		expect(validatePosition(input).valid).toBe(false);
	});
});

describe('validateDecision', () => {
	it('invalid bila tidak ada keputusan', () => {
		const res = validateDecision(makeInput());
		expect(res.valid).toBe(false);
		expect(res.issues[0].field).toBe('decisions');
	});

	it('valid dengan 1 keputusan', () => {
		const input = makeInput({ decisions: [{ type: 'loan_vs_save' }] as never });
		expect(validateDecision(input).valid).toBe(true);
	});

	it('invalid bila lebih dari 2 keputusan', () => {
		const input = makeInput({
			decisions: [{ type: 'a' }, { type: 'b' }, { type: 'c' }] as never
		});
		expect(validateDecision(input).valid).toBe(false);
	});

	it('invalid bila ada tipe keputusan duplikat', () => {
		const input = makeInput({
			decisions: [{ type: 'loan_vs_save' }, { type: 'loan_vs_save' }] as never
		});
		const res = validateDecision(input);
		expect(res.valid).toBe(false);
	});
});

describe('validateAssumption', () => {
	it('valid bila preset terisi', () => {
		expect(validateAssumption(makeInput()).valid).toBe(true);
	});

	it('invalid bila preset kosong', () => {
		const input = makeInput();
		input.preset = '';
		expect(validateAssumption(input).valid).toBe(false);
	});
});

describe('validateStep', () => {
	it('mengarahkan ke validator yang benar per langkah', () => {
		const noDecisions = makeInput();
		expect(validateStep(0, noDecisions).valid).toBe(true);
		expect(validateStep(2, noDecisions).valid).toBe(false);
	});
});
