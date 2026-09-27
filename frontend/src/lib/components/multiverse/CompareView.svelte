<script lang="ts">
	import type { Twin } from '$lib/api/types';
	import { rupiahBrief, months } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let { twins, year = 10 }: { twins: Twin[]; year?: number } = $props();

	let aCode = $state('0');
	let bCode = $state('A');

	$effect(() => {
		if (!twins.some((t) => t.code === aCode)) aCode = twins[0]?.code ?? '0';
		if (!twins.some((t) => t.code === bCode)) bCode = twins[1]?.code ?? 'A';
	});

	let a = $derived(twins.find((t) => t.code === aCode) ?? twins[0]);
	let b = $derived(twins.find((t) => t.code === bCode) ?? twins[1]);

	// wealth gap per tahun
	let gap = $derived(
		Array.from({ length: 21 }, (_, y) => {
			const av = a?.yearly_series.find((p) => p.year === y)?.net_worth ?? 0;
			const bv = b?.yearly_series.find((p) => p.year === y)?.net_worth ?? 0;
			return { year: y, diff: bv - av };
		})
	);

	const W = 600;
	const H = 200;
	const PAD = { l: 48, r: 12, t: 12, b: 26 };
	let maxAbs = $derived(Math.max(...gap.map((g) => Math.abs(g.diff)), 1));

	function x(y: number): number {
		return PAD.l + ((W - PAD.l - PAD.r) * y) / 20;
	}
	function yFor(v: number): number {
		return PAD.t + (H - PAD.t - PAD.b) / 2 - (v / maxAbs) * ((H - PAD.t - PAD.b) / 2);
	}

	let areaPath = $derived(
		`M ${x(0)} ${yFor(0)} ` +
			gap.map((g) => `L ${x(g.year).toFixed(1)} ${yFor(g.diff).toFixed(1)}`).join(' ') +
			` L ${x(20)} ${yFor(0)} Z`
	);

	function at(t: Twin | undefined, y: number) {
		return t?.yearly_series.find((p) => p.year === y);
	}

	const metrics: {
		key: string;
		label: string;
		fmt: (v: number) => string;
		get: (t: Twin | undefined) => number;
	}[] = [
		{
			key: 'net_worth',
			label: 'Net worth',
			fmt: rupiahBrief,
			get: (t) => at(t, year)?.net_worth ?? 0
		},
		{
			key: 'net_worth_real',
			label: 'Net worth riil',
			fmt: rupiahBrief,
			get: (t) => at(t, year)?.net_worth_real ?? 0
		},
		{ key: 'cash', label: 'Kas', fmt: rupiahBrief, get: (t) => at(t, year)?.cash ?? 0 },
		{ key: 'invest', label: 'Investasi', fmt: rupiahBrief, get: (t) => at(t, year)?.invest ?? 0 },
		{ key: 'debt', label: 'Sisa utang', fmt: rupiahBrief, get: (t) => at(t, year)?.debt ?? 0 },
		{
			key: 'cashflow',
			label: 'Arus kas/bln',
			fmt: rupiahBrief,
			get: (t) => at(t, year)?.cashflow ?? 0
		},
		{
			key: 'emergency',
			label: 'Dana darurat',
			fmt: months,
			get: (t) => at(t, year)?.emergency_months ?? 0
		},
		{
			key: 'score',
			label: 'Skor',
			fmt: (v) => `${(v * 100).toFixed(0)}/100`,
			get: (t) => t?.score ?? 0
		}
	];
</script>

<div class="card p-4">
	<div class="mb-3 flex flex-wrap items-center gap-3">
		<h3 class="text-sm font-semibold">Bandingkan dua twin (tahun ke-{year})</h3>
		<div class="flex items-center gap-2 text-sm">
			<select class="input !w-auto !py-1.5" bind:value={aCode} aria-label="Twin pertama">
				{#each twins as t (t.code)}<option value={t.code}>{t.label}</option>{/each}
			</select>
			<span class="text-[var(--color-ink-dim)]">vs</span>
			<select class="input !w-auto !py-1.5" bind:value={bCode} aria-label="Twin kedua">
				{#each twins as t (t.code)}<option value={t.code}>{t.label}</option>{/each}
			</select>
		</div>
	</div>

	<div class="overflow-x-auto">
		<svg
			viewBox={`0 0 ${W} ${H}`}
			class="w-full min-w-[480px]"
			role="img"
			aria-label="Selisih net worth per tahun antara dua twin"
		>
			<line
				x1={PAD.l}
				y1={yFor(0)}
				x2={W - PAD.r}
				y2={yFor(0)}
				stroke="var(--color-ink-dim)"
				stroke-width="1"
			/>
			{#each [0, 5, 10, 15, 20] as yr}
				<text
					x={x(yr)}
					y={H - PAD.b + 16}
					text-anchor="middle"
					font-size="10"
					fill="var(--color-ink-dim)">th {yr}</text
				>
			{/each}
			<path d={areaPath} fill={b?.color ?? '#34D399'} opacity="0.28" />
			<path
				d={gap.map((g, i) => `${i === 0 ? 'M' : 'L'} ${x(g.year)} ${yFor(g.diff)}`).join(' ')}
				fill="none"
				stroke={b?.color ?? '#34D399'}
				stroke-width="2.5"
			/>
			<text
				x={PAD.l - 6}
				y={yFor(maxAbs) + 4}
				text-anchor="end"
				font-size="9"
				fill="var(--color-ink-dim)"
			>
				+{rupiahBrief(maxAbs)}
			</text>
			<text
				x={PAD.l - 6}
				y={yFor(-maxAbs) + 4}
				text-anchor="end"
				font-size="9"
				fill="var(--color-ink-dim)"
			>
				-{rupiahBrief(maxAbs)}
			</text>
		</svg>
	</div>
	<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
		Area di atas garis = <strong style="color:{b?.color}">{b?.label}</strong> lebih tinggi. Di bawah
		= lebih rendah, dibanding {a?.label}.
	</p>

	<div class="mt-4 overflow-x-auto rounded-xl border border-[var(--color-line)]">
		<table class="w-full text-sm">
			<thead class="bg-[var(--color-void-2)] text-xs text-[var(--color-ink-dim)]">
				<tr>
					<th class="px-3 py-2 text-left font-medium">Metrik th {year}</th>
					<th class="px-3 py-2 text-right font-medium"
						>{twinIcon(a?.icon ?? 'circle')} {a?.label}</th
					>
					<th class="px-3 py-2 text-right font-medium"
						>{twinIcon(b?.icon ?? 'circle')} {b?.label}</th
					>
					<th class="px-3 py-2 text-right font-medium">Selisih</th>
				</tr>
			</thead>
			<tbody class="divide-y divide-[var(--color-line)]">
				{#each metrics as m}
					{@const av = m.get(a)}
					{@const bv = m.get(b)}
					{@const diff = bv - av}
					<tr>
						<td class="px-3 py-2">{m.label}</td>
						<td class="num px-3 py-2 text-right">{m.fmt(av)}</td>
						<td class="num px-3 py-2 text-right">{m.fmt(bv)}</td>
						<td
							class="num px-3 py-2 text-right"
							style="color:{diff > 0
								? 'var(--color-ok)'
								: diff < 0
									? 'var(--color-danger)'
									: 'var(--color-ink-dim)'}"
						>
							{diff > 0 ? '+' : ''}{m.fmt(diff)}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
