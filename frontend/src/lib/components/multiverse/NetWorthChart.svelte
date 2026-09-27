<script lang="ts">
	import type { Twin } from '$lib/api/types';
	import { rupiahBrief } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let {
		twins,
		selectedYear = $bindable(10),
		real = $bindable(false)
	}: {
		twins: Twin[];
		selectedYear: number;
		real: boolean;
	} = $props();

	const W = 720;
	const H = 320;
	const PAD = { l: 56, r: 16, t: 16, b: 32 };

	function valueAt(t: Twin, year: number): number {
		const p = t.yearly_series.find((s) => s.year === year);
		if (!p) return 0;
		return real ? p.net_worth_real : p.net_worth;
	}

	let maxY = $derived.by(() => {
		let m = 0;
		for (const t of twins)
			for (const p of t.yearly_series) m = Math.max(m, real ? p.net_worth_real : p.net_worth);
		return m || 1;
	});

	let minY = $derived.by(() => {
		let m = 0;
		for (const t of twins)
			for (const p of t.yearly_series) m = Math.min(m, real ? p.net_worth_real : p.net_worth);
		return m;
	});

	function x(year: number): number {
		return PAD.l + ((W - PAD.l - PAD.r) * year) / 20;
	}
	function y(v: number): number {
		const span = maxY - minY || 1;
		return H - PAD.b - ((H - PAD.t - PAD.b) * (v - minY)) / span;
	}

	function linePath(t: Twin): string {
		return t.yearly_series
			.map(
				(p, i) =>
					`${i === 0 ? 'M' : 'L'} ${x(p.year).toFixed(1)} ${y(valueAt(t, p.year)).toFixed(1)}`
			)
			.join(' ');
	}

	const dashMap: Record<string, string> = {
		solid: 'none',
		dashed: '7 4',
		dotted: '1 5',
		dashdot: '8 4 1 4',
		longdash: '14 6'
	};

	let hovered = $state<Twin | null>(null);
</script>

<div class="card p-4">
	<div class="mb-3 flex flex-wrap items-center justify-between gap-3">
		<h3 class="text-sm font-semibold">Proyeksi net worth</h3>
		<div class="flex items-center gap-2">
			<button class="chip" class:active={!real} onclick={() => (real = false)}>Nominal</button>
			<button class="chip" class:active={real} onclick={() => (real = true)}
				>Nilai riil (disesuaikan inflasi)</button
			>
		</div>
	</div>

	<div class="overflow-x-auto">
		<svg
			viewBox={`0 0 ${W} ${H}`}
			class="w-full min-w-[520px]"
			role="img"
			aria-label="Grafik net worth per twin"
		>
			<!-- gridlines -->
			{#each [0, 5, 10, 15, 20] as yr}
				<line
					x1={x(yr)}
					y1={PAD.t}
					x2={x(yr)}
					y2={H - PAD.b}
					stroke="var(--color-line)"
					stroke-width="1"
					stroke-dasharray="2 4"
				/>
				<text
					x={x(yr)}
					y={H - PAD.b + 18}
					text-anchor="middle"
					font-size="11"
					fill="var(--color-ink-dim)"
				>
					th {yr}
				</text>
			{/each}
			{#each [0, 0.5, 1] as frac}
				{@const v = minY + (maxY - minY) * frac}
				<line
					x1={PAD.l}
					y1={y(v)}
					x2={W - PAD.r}
					y2={y(v)}
					stroke="var(--color-line)"
					stroke-width="1"
				/>
				<text
					x={PAD.l - 8}
					y={y(v) + 4}
					text-anchor="end"
					font-size="10"
					fill="var(--color-ink-dim)"
				>
					{rupiahBrief(v)}
				</text>
			{/each}

			<!-- zero line -->
			{#if (minY < 0 && maxY > 0) || true}
				<line
					x1={PAD.l}
					y1={y(0)}
					x2={W - PAD.r}
					y2={y(0)}
					stroke="var(--color-ink-dim)"
					stroke-width="1"
					opacity="0.5"
				/>
			{/if}

			<!-- selected year marker -->
			<line
				x1={x(selectedYear)}
				y1={PAD.t}
				x2={x(selectedYear)}
				y2={H - PAD.b}
				stroke="var(--color-accent)"
				stroke-width="1.5"
			/>

			<!-- twin lines -->
			{#each twins as t (t.code)}
				<path
					d={linePath(t)}
					fill="none"
					stroke={t.color}
					stroke-width={hovered?.code === t.code ? 3.5 : 2.5}
					stroke-dasharray={dashMap[t.dash] ?? 'none'}
					stroke-linejoin="round"
					stroke-linecap="round"
				/>
				<circle
					cx={x(selectedYear)}
					cy={y(valueAt(t, selectedYear))}
					r="4.5"
					fill={t.color}
					stroke="var(--color-void)"
					stroke-width="2"
				/>
			{/each}
		</svg>
	</div>

	<!-- legend (warna + pola garis + ikon) -->
	<div class="mt-3 flex flex-wrap gap-3">
		{#each twins as t (t.code)}
			<button
				class="flex items-center gap-2 rounded-lg px-2 py-1 text-xs hover:bg-[var(--color-void-2)]"
				onmouseenter={() => (hovered = t)}
				onmouseleave={() => (hovered = null)}
			>
				<svg width="24" height="10" aria-hidden="true">
					<line
						x1="0"
						y1="5"
						x2="24"
						y2="5"
						stroke={t.color}
						stroke-width="3"
						stroke-dasharray={dashMap[t.dash] ?? 'none'}
					/>
				</svg>
				<span class="font-medium">{twinIcon(t.icon)} {t.label}</span>
				<span class="num text-[var(--color-ink-dim)]">{rupiahBrief(valueAt(t, selectedYear))}</span>
			</button>
		{/each}
	</div>

	<!-- tabel alternatif (aksesibilitas) -->
	<details class="mt-3">
		<summary class="cursor-pointer text-xs text-[var(--color-ink-dim)]">Lihat tabel data</summary>
		<div class="mt-2 overflow-x-auto">
			<table class="w-full text-xs">
				<thead class="text-[var(--color-ink-dim)]">
					<tr>
						<th class="px-2 py-1 text-left">Twin</th>
						{#each [5, 10, 15, 20] as yr}<th class="px-2 py-1 text-right">th {yr}</th>{/each}
					</tr>
				</thead>
				<tbody>
					{#each twins as t (t.code)}
						<tr>
							<td class="px-2 py-1">{t.label}</td>
							{#each [5, 10, 15, 20] as yr}<td class="num px-2 py-1 text-right"
									>{rupiahBrief(valueAt(t, yr))}</td
								>{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</details>
</div>
