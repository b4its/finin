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
	/** True selama narasi SSE masih mengalir (untuk indikator "menulis narasi…"). */
	narrating = $state(false);
	errorMsg = $state<string | null>(null);
	fscPre = $state<number | null>(null);

	/**
	 * Token generasi narasi. Setiap panggilan streamNarration menaikkan nilai ini;
	 * hanya stream dengan token terbaru yang boleh menulis ke state. Ini mencegah
	 * race condition ketika pengguna mengganti preset cepat sementara stream lama
	 * masih mengalir (chunk lama tidak lagi menimpa hasil baru).
	 */
	#narrationGen = 0;
	#recomputeGen = 0;

	async loadAssumptions(force = false) {
		if (this.assumptions && !force) return;
		try {
			this.assumptions = await api.assumptions(this.input.preset);
		} catch (e) {
			this.errorMsg = String(e);
		}
	}

	reset() {
		this.#narrationGen++;
		this.#recomputeGen++;
		this.input = structuredClone(DEFAULT_INPUT);
		this.result = null;
		this.recommendation = null;
		this.narrative = {};
		this.narrating = false;
		this.errorMsg = null;
		this.fscPre = null;
	}

	async simulate() {
		this.loading = true;
		this.errorMsg = null;
		try {
			const res = await api.createSimulation(this.input);
			this.result = res;
			const bestTwin = res.twins.find((t) => t.code === res.best_twin);
			const y10 = bestTwin?.yearly_series.find((p) => p.year === 10);
			history.add({
				id: res.id,
				twin_count: res.twins.length,
				best_twin: res.best_twin,
				preset: res.preset,
				label: this.describeInput(),
				best_net_worth_y10: y10?.net_worth_real,
				income_monthly: this.input.profile.income_monthly
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
		const generation = ++this.#recomputeGen;
		const simulationId = this.result.id;
		this.loading = true;
		this.errorMsg = null;
		try {
			const res = await api.recompute(simulationId, {
				preset: preset ?? this.result.preset,
				assumption_overrides: overrides
			});
			if (generation !== this.#recomputeGen) return;
			this.result = res;
			// Hitung ulang mengubah angka, jadi narasi & rekomendasi harus segar.
			this.narrative = {};
			this.recommendation = null;
			this.streamNarration(res.id);
			api
				.recommendation(res.id)
				.then((r) => {
					if (generation === this.#recomputeGen) this.recommendation = r;
				})
				.catch(() => {
					if (generation === this.#recomputeGen) this.recommendation = null;
				});
		} catch (e) {
			if (generation === this.#recomputeGen) this.errorMsg = String(e);
		} finally {
			if (generation === this.#recomputeGen) this.loading = false;
		}
	}

	private async streamNarration(id: string) {
		const gen = ++this.#narrationGen;
		const map: Record<string, NarrativeChunk[]> = {};
		this.narrating = true;
		try {
			await streamNarrative(
				id,
				(chunk) => {
					if (gen !== this.#narrationGen) return; // stream usang -> abaikan
					(map[chunk.twin] ||= []).push(chunk);
					this.narrative = { ...map };
				},
				() => {
					if (gen !== this.#narrationGen) return;
					this.narrative = { ...map };
				}
			);
		} catch {
			/* narasi gagal stream -> tetap jalan */
		} finally {
			// Hanya stream terbaru yang boleh mematikan indikator.
			if (gen === this.#narrationGen) this.narrating = false;
		}
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
