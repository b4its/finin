/**
 * Validasi tiap langkah wizard — satu sumber kebenaran.
 *
 * Mengembalikan daftar masalah per langkah sehingga tombol "Lanjut" bisa
 * dinonaktifkan dengan alasan yang jelas (bukan hanya true/false yang tak
 * terlihat pengguna). Semua pesan berbahasa Indonesia.
 */

import type { SimulationInput } from '$lib/api/client';

export interface ValidationIssue {
	field: string;
	message: string;
	/** Warning memberi konteks tetapi tidak mengunci navigasi wizard. */
	blocking?: boolean;
}

export interface StepValidation {
	valid: boolean;
	issues: ValidationIssue[];
}

const MIN_AGE = 15;
const MAX_AGE = 60;

function salaryLike(incomeType: string): boolean {
	return incomeType === 'salary' || incomeType === 'allowance';
}

/** Langkah 1 — Penghasilan. */
export function validateIncome(input: SimulationInput): StepValidation {
	const issues: ValidationIssue[] = [];
	const p = input.profile;
	if (salaryLike(p.income_type) && p.income_monthly <= 0) {
		issues.push({
			field: 'income_monthly',
			message: 'Penghasilan bulanan harus lebih dari 0 untuk tipe penghasilan tetap.'
		});
	}
	if (p.expense_monthly < 0) {
		issues.push({ field: 'expense_monthly', message: 'Pengeluaran tidak boleh negatif.' });
	}
	if (p.income_type === 'variable') {
		if (p.income_range && p.income_range.max < p.income_range.min) {
			issues.push({
				field: 'income_range',
				message: 'Batas atas rentang penghasilan lebih kecil dari batas bawah.'
			});
		}
	}
	if (p.expense_monthly > p.income_monthly && p.income_monthly > 0) {
		issues.push({
			field: 'expense_monthly',
			message:
				'Pengeluaran melebihi penghasilan — simulasi tetap bisa jalan, tapi ingat ini defisit.',
			blocking: false
		});
	}
	return { valid: issues.every((issue) => issue.blocking === false), issues };
}

/** Langkah 2 — Posisi. */
export function validatePosition(input: SimulationInput): StepValidation {
	const issues: ValidationIssue[] = [];
	const p = input.profile;
	if (!Number.isFinite(p.age) || p.age < MIN_AGE || p.age > MAX_AGE) {
		issues.push({ field: 'age', message: `Usia harus antara ${MIN_AGE}–${MAX_AGE} tahun.` });
	}
	if (p.savings < 0) {
		issues.push({ field: 'savings', message: 'Tabungan tidak boleh negatif.' });
	}
	if (p.dependents_monthly < 0) {
		issues.push({ field: 'dependents_monthly', message: 'Tanggungan tidak boleh negatif.' });
	}
	if (p.existing_debt.monthly_payment < 0) {
		issues.push({ field: 'debt', message: 'Cicilan berjalan tidak boleh negatif.' });
	}
	return { valid: issues.length === 0, issues };
}

/** Langkah 3 — Keputusan. */
export function validateDecision(input: SimulationInput): StepValidation {
	const issues: ValidationIssue[] = [];
	const decisions = input.decisions ?? [];
	if (decisions.length < 1) {
		issues.push({ field: 'decisions', message: 'Pilih minimal 1 keputusan untuk dibandingkan.' });
	}
	if (decisions.length > 2) {
		issues.push({ field: 'decisions', message: 'Maksimal 2 keputusan dalam satu simulasi.' });
	}
	const types = decisions.map((d) => d.type);
	if (new Set(types).size !== types.length) {
		issues.push({ field: 'decisions', message: 'Setiap keputusan harus bertipe berbeda.' });
	}
	return { valid: issues.length === 0, issues };
}

/** Langkah 4 — Asumsi. */
export function validateAssumption(input: SimulationInput): StepValidation {
	const issues: ValidationIssue[] = [];
	if (!input.preset) {
		issues.push({ field: 'preset', message: 'Pilih salah satu preset asumsi.' });
	}
	return { valid: issues.length === 0, issues };
}

export type WizardStep = 0 | 1 | 2 | 3;
/** Indeks langkah wizard termasuk langkah ringkasan (review). */
export type WizardUiStep = WizardStep | 4;

/** Validasi untuk indeks langkah tertentu. */
export function validateStep(step: WizardStep, input: SimulationInput): StepValidation {
	switch (step) {
		case 0:
			return validateIncome(input);
		case 1:
			return validatePosition(input);
		case 2:
			return validateDecision(input);
		case 3:
			return validateAssumption(input);
	}
}
