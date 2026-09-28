/** Store simulasi (Svelte 5 runes) — menyimpan input wizard & hasil. */

import { api, streamNarrative, type SimulationInput } from '$lib/api/client';
import { history } from '$lib/stores/history.svelte';
import { rupiahBrief } from '$lib/utils/format';
import type {
	AssumptionsSnapshot,
	NarrativeChunk,
	Recommendation,
	Simulation
} from '$lib/api/types';

export const DEFAULT_INPUT: SimulationInput = {
	profile: {
		age: 22,
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
	assumption_overrides: {}
};

class SimulationStore {
	input = $state<SimulationInput>(structuredClone(DEFAULT_INPUT));
	assumptions = $state<AssumptionsSnapshot | null>(null);
	result = $state<Simulation | null>(null);
	recommendation = $state<Recommendation | null>(null);
	narrative = $state<Record<string, NarrativeChunk[]>>({});
	loading = $state(false);
	errorMsg = $state<string | null>(null);
	fscPre = $state<number | null>(null);
	fscPost = $state<number | null>(null);

	async loadAssumptions() {
		if (this.assumptions) return;
		try {
			const a = await api.assumptions(this.input.preset);
			this.assumptions = a;
		} catch (e) {
			this.errorMsg = String(e);
		}
	}

	reset() {
		this.input = structuredClone(DEFAULT_INPUT);
		this.result = null;
		this.recommendation = null;
		this.narrative = {};
		this.errorMsg = null;
		this.fscPre = null;
		this.fscPost = null;
	}

	async simulate() {
		this.loading = true;
		this.errorMsg = null;
		try {
			const res = await api.createSimulation(this.input);
			this.result = res;
			history.add({
				id: res.id,
				twin_count: res.twins.length,
				best_twin: res.best_twin,
				preset: res.preset,
				label: this.describeInput()
			});
			// mulai stream narasi + rekomendasi secara paralel
			this.streamNarration(res.id);
			api
				.recommendation(res.id)
				.then((r) => (this.recommendation = r))
				.catch(() => (this.recommendation = null));
			return res;
		} catch (e) {
			this.errorMsg = String(e);
			throw e;
		} finally {
			this.loading = false;
		}
	}

	async recompute(preset?: string, overrides: Record<string, unknown> = {}) {
		if (!this.result) return;
		this.loading = true;
		try {
			const res = await api.recompute(this.result.id, {
				preset: preset ?? this.result.preset,
				assumption_overrides: overrides
			});
			this.result = res;
			// Hitung ulang mengubah angka, jadi narasi & rekomendasi harus segar.
			this.narrative = {};
			this.recommendation = null;
			this.streamNarration(res.id);
			api
				.recommendation(res.id)
				.then((r) => (this.recommendation = r))
				.catch(() => (this.recommendation = null));
		} catch (e) {
			this.errorMsg = String(e);
		} finally {
			this.loading = false;
		}
	}

	private async streamNarration(id: string) {
		const map: Record<string, NarrativeChunk[]> = {};
		try {
			await streamNarrative(
				id,
				(chunk) => {
					(map[chunk.twin] ||= []).push(chunk);
					this.narrative = { ...map };
				},
				() => {
					this.narrative = { ...map };
				}
			);
		} catch {
			/* narasi gagal stream -> tetap jalan */
		}
	}

	async commit() {
		if (!this.result) return;
		await api.recordEvent(this.result.id, 'commit');
	}

	textForTwin(twinCode: string, horizon: number): string | null {
		const chunks = this.narrative[twinCode];
		if (!chunks) return null;
		return chunks.find((c) => c.horizon === horizon)?.text ?? null;
	}

	/** Ringkasan manusiawi dari input untuk label riwayat. */
	describeInput(): string {
		const dec = this.input.decisions.map((d) => d.type.replace(/_/g, ' ')).join(', ');
		const income = rupiahBrief(this.input.profile.income_monthly);
		return dec ? `${income}/bln · ${dec}` : `${income}/bln · tanpa keputusan`;
	}
}

export const sim = new SimulationStore();
