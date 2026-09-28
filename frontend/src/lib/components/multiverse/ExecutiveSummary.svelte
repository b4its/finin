<script lang="ts">
	/**
	 * Ringkasan eksekutif: satu kartu yang merangkum keputusan terbaik, selisih
	 * kekayaan vs. baseline, ketahanan (stress), status robust, dan flag OJK.
	 * Semua angka diturunkan dari data simulasi — tidak ada perhitungan baru.
	 */
	import type { Recommendation, Twin } from '$lib/api/types';
	import { rupiahBrief, months, percent } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let {
		twins,
		recommendation = null,
		robust = false,
		robustReason = '',
		year = 10,
		flagsCount = 0,
		onOpenTwin
	}: {
		twins: Twin[];
		recommendation?: Recommendation | null;
		robust?: boolean;
		robustReason?: string;
		year?: number;
		flagsCount?: number;
		onOpenTwin?: (code: string) => void;
	} = $props();

	let bestCode = $derived(recommendation?.best_twin ?? null);
	let best = $derived(twins.find((t) => t.code === bestCode) ?? null);
	let baseline = $derived(twins.find((t) => t.code === '0') ?? null);

	function pointAt(t: Twin | null, y: number) {
		return t?.yearly_series.find((p) => p.year === y) ?? null;
	}

	let bestPoint = $derived(pointAt(best, year));
	let basePoint = $derived(pointAt(baseline, year));

	let wealthGap = $derived(bestPoint && basePoint ? bestPoint.net_worth - basePoint.net_worth : 0);
	let gapPct = $derived(
		basePoint && basePoint.net_worth !== 0 ? wealthGap / Math.abs(basePoint.net_worth) : 0
	);

	// Jumlah skenario guncangan yang lolos oleh twin terbaik.
	let stressPassed = $derived(best ? best.stress.filter((s) => s.survived).length : 0);
	let stressTotal = $derived(best?.stress.length ?? 0);

	// Berapa banyak twin yang memenuhi aturan keras (tidak dikeluarkan).
	let eligibleCount = $derived(
		twins.filter((t) => !t.deleted_by_hard_rule && t.code !== '0').length
	);

	let slikRisk = $derived(twins.some((t) => t.flags.some((f) => f.code === 'SLIK_DEFAULT')));
</script>

<section
	class="card overflow-hidden p-0"
	style="border-color: {best?.color ?? 'var(--color-line)'}"
>
	<div class="border-b border-[var(--color-line)] bg-[var(--color-void-2)] px-5 py-3">
		<div class="flex flex-wrap items-center justify-between gap-2">
			<div class="flex items-center gap-2">
				<span class="text-lg" aria-hidden="true">🧭</span>
				<h2 class="text-sm font-bold">Ringkasan eksekutif — tahun ke-{year}</h2>
			</div>
			<div class="flex flex-wrap items-center gap-1.5">
				<span
					class="chip {robust
						? 'border-[var(--color-ok)] text-[var(--color-ok)]'
						: 'border-[var(--color-warn)] text-[var(--color-warn)]'}"
				>
					{robust ? '✓ robust' : '⚠ bergantung asumsi'}
				</span>
				{#if flagsCount > 0}
					<span class="chip border-[var(--color-danger)] text-[var(--color-danger)]"
						>🚩 {flagsCount} flag OJK</span
					>
				{:else}
					<span class="chip border-[var(--color-ok)] text-[var(--color-ok)]">✓ bebas flag OJK</span>
				{/if}
			</div>
		</div>
	</div>

	<div class="grid grid-cols-2 gap-px bg-[var(--color-line)] sm:grid-cols-4">
		<div class="bg-[var(--color-panel)] p-4">
			<div class="text-[11px] uppercase tracking-wide text-[var(--color-ink-dim)]">
				Cabang terbaik
			</div>
			{#if best}
				<button
					class="mt-1 flex items-center gap-1.5 text-left text-base font-bold hover:underline"
					onclick={() => onOpenTwin?.(best!.code)}
				>
					<span aria-hidden="true">{twinIcon(best.icon)}</span>
					<span style="color:{best.color}">{best.label}</span>
				</button>
				<div class="num mt-0.5 text-xs text-[var(--color-ink-dim)]">
					skor {(best.score * 100).toFixed(0)}/100
				</div>
			{:else}
				<div class="mt-1 text-sm text-[var(--color-ink-dim)]">Menghitung…</div>
			{/if}
		</div>

		<div class="bg-[var(--color-panel)] p-4">
			<div class="text-[11px] uppercase tracking-wide text-[var(--color-ink-dim)]">
				Selisih vs baseline
			</div>
			<div
				class="num mt-1 text-base font-bold {wealthGap >= 0
					? 'text-[var(--color-ok)]'
					: 'text-[var(--color-danger)]'}"
			>
				{wealthGap >= 0 ? '+' : ''}{rupiahBrief(wealthGap)}
			</div>
			<div class="num mt-0.5 text-xs text-[var(--color-ink-dim)]">
				{wealthGap >= 0 ? '+' : ''}{percent(gapPct, 0)} vs “tanpa perubahan”
			</div>
		</div>

		<div class="bg-[var(--color-panel)] p-4">
			<div class="text-[11px] uppercase tracking-wide text-[var(--color-ink-dim)]">
				Dana darurat th-{year}
			</div>
			<div class="num mt-1 text-base font-bold">
				{bestPoint ? months(bestPoint.emergency_months) : '—'}
			</div>
			<div class="mt-0.5 text-xs text-[var(--color-ink-dim)]">
				DSR {bestPoint ? percent(bestPoint.dsr, 0) : '—'}
			</div>
		</div>

		<div class="bg-[var(--color-panel)] p-4">
			<div class="text-[11px] uppercase tracking-wide text-[var(--color-ink-dim)]">
				Lolos stress test
			</div>
			<div class="num mt-1 text-base font-bold">
				{stressPassed}/{stressTotal}
			</div>
			<div class="mt-0.5 text-xs text-[var(--color-ink-dim)]">
				{eligibleCount} cabang lolos aturan keras
			</div>
		</div>
	</div>

	{#if robustReason || slikRisk}
		<div class="border-t border-[var(--color-line)] px-5 py-3 text-xs text-[var(--color-ink-dim)]">
			{#if robustReason}
				<span>📊 {robustReason}</span>
			{/if}
			{#if slikRisk}
				<span class="ml-1 text-[var(--color-warn)]"
					>· ⚠ setidaknya satu cabang berisiko tercatat di SLIK OJK.</span
				>
			{/if}
		</div>
	{/if}
</section>
