<script lang="ts">
	let {
		year = $bindable(10),
		// narasi opsional per tahun
		narration = null as string | null
	}: { year: number; narration?: string | null } = $props();

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
	/>
	{#if narration}
		<p
			class="mt-3 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3 text-sm leading-relaxed"
		>
			{narration}
		</p>
	{/if}
</div>
