<script lang="ts">
	import Badge from '$lib/components/ui/Badge.svelte';
	import Tooltip from '$lib/components/ui/Tooltip.svelte';
	import type { Twin } from '$lib/api/types';
	import { rupiahBrief, months, percent } from '$lib/utils/format';
	import { twinIcon, twinIconLabel } from '$lib/utils/icons';

	let {
		twin,
		year = 10,
		narrative = null,
		isBest = false,
		onSelect
	}: {
		twin: Twin;
		year?: number;
		narrative?: string | null;
		isBest?: boolean;
		onSelect?: (t: Twin) => void;
	} = $props();

	let point = $derived(twin.yearly_series.find((p) => p.year === year) ?? twin.yearly_series[0]);
	let defaulted = $derived(point?.defaulted ?? false);
	let slik = $derived(twin.flags.some((f) => f.code === 'SLIK_DEFAULT'));

	function flagsByLevel(level: string) {
		return twin.flags.filter((f) => f.level === level);
	}
</script>

<button
	type="button"
	class="card w-full p-4 text-left transition-all hover:-translate-y-0.5"
	style="border-left: 3px solid {twin.color}"
	onclick={() => onSelect?.(twin)}
>
	<div class="flex items-start justify-between gap-2">
		<div class="flex items-center gap-2">
			<span
				class="inline-flex h-6 w-6 items-center justify-center rounded-full text-sm"
				style="background:{twin.color}22; color:{twin.color}"
				aria-hidden="true">{twinIcon(twin.icon)}</span
			>
			<div>
				<div class="text-sm font-bold">{twin.label}</div>
				<div class="text-xs text-[var(--color-ink-dim)]">
					Twin {twin.code} · {twinIconLabel(twin.icon)}
				</div>
			</div>
		</div>
		<div class="flex flex-col items-end gap-1">
			{#if isBest}<Badge level="ok">Terbaik</Badge>{/if}
			{#if twin.deleted_by_hard_rule}
				<Tooltip text="Dikeluarkan dari rekomendasi karena melanggar aturan keras (macet atau DSR > 30% lebih dari 6 bulan).">
					<Badge level="red">Aturan keras</Badge>
				</Tooltip>
			{/if}
		</div>
	</div>

	<div class="mt-3 grid grid-cols-2 gap-3">
		<div>
			<div class="text-xs text-[var(--color-ink-dim)]">Net worth th {year}</div>
			<div class="num text-lg font-bold">{rupiahBrief(point.net_worth)}</div>
		</div>
		<div>
			<div class="text-xs text-[var(--color-ink-dim)]">Dana darurat</div>
			<div class="num text-lg font-bold">{months(point.emergency_months)}</div>
		</div>
	</div>

	<div class="mt-2 flex flex-wrap gap-1.5 text-xs text-[var(--color-ink-dim)]">
		<span class="num">Utang {rupiahBrief(point.debt)}</span>
		<span>·</span>
		<span class="num">DSR {percent(point.dsr, 0)}</span>
		<span>·</span>
		<span class="num">Skor {(twin.score * 100).toFixed(0)}</span>
	</div>

	{#if defaulted || slik || flagsByLevel('red').length || flagsByLevel('orange').length}
		<div class="mt-3 flex flex-wrap gap-1.5">
			{#if defaulted || slik}
				<Tooltip text="Tercatat di SLIK OJK; akses kredit formal (misalnya KPR) bisa terhambat.">
					<Badge level="yellow">SLIK</Badge>
				</Tooltip>
			{/if}
			{#each flagsByLevel('red') as f (f.code)}<Badge level="red">Di atas batas OJK</Badge>{/each}
			{#each flagsByLevel('orange') as f (f.code)}<Badge level="orange">DSR &gt; 30%</Badge>{/each}
		</div>
	{/if}

	{#if narrative}
		<p
			class="mt-3 border-t border-[var(--color-line)] pt-2 text-xs leading-relaxed text-[var(--color-ink-dim)]"
		>
			{narrative}
		</p>
	{/if}
</button>
