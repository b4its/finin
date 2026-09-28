/** Klien API Financial Twin. */

import { env } from '$env/dynamic/public';
import type {
	AssumptionsSnapshot,
	Decision,
	DecisionTemplate,
	Flag,
	NarrativeChunk,
	Recommendation,
	Simulation,
	MonteCarloResult
} from './types';

function baseUrl(): string {
	// Normalisasi: buang garis miring di akhir agar tidak muncul '//api/v1'.
	return (env.PUBLIC_API_URL || 'http://localhost:8072').replace(/\/+$/, '');
}

const API = '/api/v1';

/** Bentuk respons endpoint /health. */
export interface HealthStatus {
	status: string;
	time: string;
	engine_version: string;
	assumption_set: string;
	llm_enabled: boolean;
}

/**
 * Gabungkan sinyal AbortSignal eksternal dengan timeout internal, sehingga
 * permintaan yang menggantung tidak membuat UI "loading" selamanya.
 */
function withTimeout(
	init: RequestInit | undefined,
	ms: number
): { init: RequestInit; clear: () => void } {
	const ctrl = new AbortController();
	const timer = setTimeout(() => ctrl.abort(new DOMException('timeout', 'TimeoutError')), ms);
	const external = init?.signal;
	if (external) {
		if (external.aborted) ctrl.abort(external.reason);
		else external.addEventListener('abort', () => ctrl.abort(external.reason), { once: true });
	}
	return { init: { ...init, signal: ctrl.signal }, clear: () => clearTimeout(timer) };
}

async function request<T>(path: string, init?: RequestInit, timeoutMs = 30_000): Promise<T> {
	const { init: mergedInit, clear } = withTimeout(init, timeoutMs);
	try {
		const res = await fetch(`${baseUrl()}${API}${path}`, {
			headers: { 'Content-Type': 'application/json' },
			...mergedInit
		});
		if (!res.ok) {
			let detail: unknown = null;
			try {
				detail = await res.json();
			} catch {
				detail = await res.text();
			}
			throw new Error(`API ${res.status}: ${JSON.stringify(detail)}`);
		}
		return (await res.json()) as T;
	} finally {
		clear();
	}
}

export interface SimulationInput {
	profile: {
		age: number;
		income_type: string;
		income_monthly: number;
		income_range: { min: number; max: number } | null;
		expense_monthly: number;
		dependents_monthly: number;
		savings: number;
		existing_debt: {
			principal: number;
			monthly_payment: number;
			annual_rate: number;
			tenor_months: number;
		};
	};
	decisions: Decision[];
	preset: string;
	assumption_overrides: Record<string, unknown>;
}

export const api = {
	health: (init?: RequestInit) => request<HealthStatus>('/health', init),
	assumptions: (preset = 'moderat') =>
		request<AssumptionsSnapshot & { presets_available: string[] }>(
			`/assumptions/default?preset=${preset}`
		),
	templates: () => request<{ templates: DecisionTemplate[] }>('/templates'),
	regulatoryCheck: (body: Record<string, unknown>) =>
		request<{
			flags: Flag[];
			rate_cap_daily: number;
			installment: number;
			dsr: number;
			dsr_cap: number;
		}>('/regulatory/check', { method: 'POST', body: JSON.stringify(body) }),
	createSimulation: (body: SimulationInput) =>
		request<Simulation>('/simulations', { method: 'POST', body: JSON.stringify(body) }),
	getSimulation: (id: string) => request<Simulation>(`/simulations/${id}`),
	recompute: (
		id: string,
		body: { preset?: string; assumption_overrides?: Record<string, unknown> }
	) =>
		request<Simulation>(`/simulations/${id}/recompute`, {
			method: 'POST',
			body: JSON.stringify(body)
		}),
	recommendation: (id: string) => request<Recommendation>(`/simulations/${id}/recommendation`),
	recordEvent: (id: string, kind: string, value?: number) =>
		request<{ id: number }>(`/simulations/${id}/events`, {
			method: 'POST',
			body: JSON.stringify({ kind, value })
		}),
	impactSummary: () =>
		request<{
			fsc_pre_avg: number | null;
			fsc_post_avg: number | null;
			fsc_delta: number | null;
			commits: number;
			simulations: number;
			commit_rate: number | null;
		}>('/impact/summary'),
	exportCsvUrl: (id: string) => `${baseUrl()}${API}/simulations/${id}/export/csv`,
	exportJsonUrl: (id: string) => `${baseUrl()}${API}/simulations/${id}/export/json`,
	getMonteCarlo: (id: string, twinCode: string = '0', runs: number = 500, preset?: string) => {
		const p = new URLSearchParams({ twin_code: twinCode, runs: String(runs) });
		if (preset) p.set('preset', preset);
		return request<MonteCarloResult>(`/simulations/${id}/monte-carlo?${p.toString()}`);
	}
};

/** Stream narasi (SSE) dengan EventSource-like parsing via fetch. */
export async function streamNarrative(
	simId: string,
	onChunk: (chunk: NarrativeChunk) => void,
	onDone: () => void
): Promise<void> {
	const res = await fetch(`${baseUrl()}${API}/simulations/${simId}/narrative`);
	if (!res.body) {
		onDone();
		return;
	}
	const reader = res.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';
	while (true) {
		const { done, value } = await reader.read();
		if (done) break;
		buffer += decoder.decode(value, { stream: true });
		const lines = buffer.split('\n\n');
		buffer = lines.pop() ?? '';
		for (const block of lines) {
			const dataLine = block.split('\n').find((l) => l.startsWith('data:'));
			if (!dataLine) continue;
			try {
				const payload = JSON.parse(dataLine.slice(5).trim());
				if (payload.done) {
					onDone();
					return;
				}
				onChunk(payload as NarrativeChunk);
			} catch {
				/* abaikan blok yang tidak valid */
			}
		}
	}
	onDone();
}
