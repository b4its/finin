<script lang="ts">
	import type { Twin } from '$lib/api/types';
	import { rupiahBrief } from '$lib/utils/format';

	let {
		twins,
		selectedYear = 10,
		brokenShock = null as string | null
	}: { twins: Twin[]; selectedYear: number; brokenShock?: string | null } = $props();

	// layout: root di kiri, cabang di kanan
	const rowH = 96;
	const height = $derived(Math.max(twins.length * rowH, 240));
	const W = 640;
	const rootX = 70;
	const nodeX = [220, 400, 580];
	const years = [5, 10, 20];

	let hovered = $state<number | null>(null);

	function yFor(i: number): number {
		return 40 + i * rowH;
	}
	function valueAt(t: Twin, y: number): number {
		return t.yearly_series.find((p) => p.year === y)?.net_worth ?? 0;
	}
	function isBroken(t: Twin): boolean {
		if (!brokenShock) return false;
		const s = t.stress.find((x) => x.shock === brokenShock);
		return s ? !s.survived : false;
	}
</script>

<div class="card overflow-x-auto p-4">
	<h3 class="mb-2 text-sm font-semibold">Multiverse — cabang masa depanmu</h3>
	<svg
		viewBox={`0 0 ${W} ${height}`}
		class="w-full min-w-[560px]"
		role="img"
		aria-label="Diagram cabang masa depan"
	>
		<!-- root -->
		<g>
			<circle cx={rootX} cy={height / 2} r="9" fill="var(--color-accent)" />
			<text
				x={rootX}
				y={height / 2 + 26}
				text-anchor="middle"
				font-size="12"
				font-weight="600"
				fill="var(--color-ink)"
			>
				Kamu hari ini
			</text>
		</g>

		<!-- kolom tahun -->
		{#each years as yr, ci}
			<text x={nodeX[ci]} y="18" text-anchor="middle" font-size="11" fill="var(--color-ink-dim)"
				>Tahun {yr}</text
			>
		{/each}

		{#each twins as t, i (t.code)}
			{@const ty = yFor(i)}
			{@const broken = isBroken(t)}
			<!-- garis dari root -->
			<path
				d={`M ${rootX + 9} ${height / 2} C ${rootX + 60} ${height / 2}, ${nodeX[0] - 70} ${ty}, ${nodeX[0]} ${ty}`}
				fill="none"
				stroke={t.color}
				stroke-width={hovered === i ? 3 : 1.8}
				stroke-dasharray={broken ? '5 5' : 'none'}
				opacity={broken ? 0.5 : 0.9}
			/>
			{#each years as yr, ci}
				{@const nx = nodeX[ci]}
				{#if ci > 0}
					<line
						x1={nodeX[ci - 1]}
						y1={ty}
						x2={nx}
						y2={ty}
						stroke={t.color}
						stroke-width="1.6"
						stroke-dasharray={broken ? '5 5' : 'none'}
						opacity={broken ? 0.45 : 0.85}
					/>
				{/if}
				<circle
					cx={nx}
					cy={ty}
					r={ci === 1 ? 6 : 4.5}
					fill={broken ? 'var(--color-void-2)' : t.color}
					stroke={t.color}
					stroke-width="2"
					role="presentation"
					onmouseenter={() => (hovered = i)}
					onmouseleave={() => (hovered = null)}
				/>
				<text
					x={nx}
					y={ty - 10}
					text-anchor="middle"
					font-size="10"
					class="num"
					fill="var(--color-ink-dim)"
				>
					{rupiahBrief(valueAt(t, yr))}
				</text>
			{/each}
			<!-- label -->
			<text x={rootX + 16} y={ty + 4} font-size="11" font-weight="600" fill={t.color}>
				{t.label}
			</text>
			{#if broken}
				<text
					x={nodeX[2]}
					y={ty + 22}
					text-anchor="middle"
					font-size="10"
					fill="var(--color-danger)"
				>
					✕ tidak bertahan
				</text>
			{/if}
		{/each}
	</svg>
	<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
		Titik tengah = tahun ke-{selectedYear} (disorot). Garis putus-putus = skenario guncangan yang membuat
		cabang tidak bertahan.
	</p>
</div>
