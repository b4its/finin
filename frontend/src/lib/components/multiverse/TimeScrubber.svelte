<script lang="ts">
	import type { Twin } from '$lib/api/types';

	let {
		year = $bindable(10),
		twins = [] as Twin[],
		narration = null as string | null,
		onFocusTwin
	}: {
		year: number;
		twins?: Twin[];
		narration?: string | null;
		onFocusTwin?: (code: string) => void;
	} = $props();

	const marks = [0, 5, 10, 15, 20];
</script>

<div class="card p-4">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div>
			<div class="text-xs text-[var(--color-ink-dim)]">Geser waktu</div>
			<div class="num text-lg font-bold">Tahun ke-{year}</div>
		</div>
		<div class="flex gap-1.5">
			{#each marks as m}
				<button class="chip" class:active={year === m} onclick={() => (year = m)}>th {m}</button>
			{/each}
		</div>
	</div>
	<input
		type="range"
		min="0"
		max="20"
		step="1"
		value={year}
		oninput={(e) => (year = parseInt((e.target as HTMLInputElement).value))}
		class="mt-4 w-full accent-[var(--color-accent)]"
		aria-label="Pilih tahun proyeksi"
		aria-valuetext="Tahun ke-{year}"
	/>

	{#if twins.length > 0}
		<div class="mt-3 flex flex-wrap gap-1.5">
			<span class="text-xs text-[var(--color-ink-dim)]">Narasi twin:</span>
			{#each twins as t (t.code)}
				<button
					class="chip"
					style="border-color:{t.color}"
					onclick={() => onFocusTwin?.(t.code)}
				>
					<span class="inline-block h-2 w-2 rounded-full" style="background:{t.color}"></span>
					{t.label}
				</button>
			{/each}
		</div>
	{/if}

	{#if narration}
		<p class="mt-3 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3 text-sm leading-relaxed">
			{narration}
		</p>
	{:else}
		<p class="mt-3 text-xs text-[var(--color-ink-dim)]">
			Narasi tersedia pada horizon tahun ke-5, 10, dan 20 — geser atau pilih salah satunya.
		</p>
	{/if}
</div>
