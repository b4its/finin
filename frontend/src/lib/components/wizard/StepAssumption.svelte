<script lang="ts">
	import Tooltip from '$lib/components/ui/Tooltip.svelte';
	import { percent, dateID, isStale } from '$lib/utils/format';
	import { sim } from '$lib/stores/simulation.svelte';

	const PRESETS = [
		{ value: 'konservatif', label: 'Konservatif', desc: 'Inflasi tinggi, imbal hasil rendah' },
		{ value: 'moderat', label: 'Moderat', desc: 'Asumsi tengah (default)' },
		{ value: 'optimis', label: 'Optimis', desc: 'Inflasi rendah, imbal hasil tinggi' }
	];

	let a = $derived(sim.assumptions);
	let stale = $derived(a ? isStale(a.as_of) : false);

	async function pickPreset(p: string) {
		sim.input.preset = p;
		await sim.loadAssumptions();
		const fresh = await (await import('$lib/api/client')).api.assumptions(p);
		sim.assumptions = fresh;
	}
</script>

<div class="space-y-6">
	<div>
		<h3 class="text-lg font-bold">Asumsi makro</h3>
		<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
			Pilih preset, atau biarkan default. Semua nilai punya sumber dan tanggal.
		</p>
	</div>

	<div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
		{#each PRESETS as p}
			<button
				type="button"
				class="rounded-xl border p-3 text-left transition-colors"
				class:active={sim.input.preset === p.value}
				class:selected={sim.input.preset === p.value}
				class:muted={sim.input.preset !== p.value}
				onclick={() => pickPreset(p.value)}
			>
				<div class="text-sm font-semibold">{p.label}</div>
				<div class="text-xs text-[var(--color-ink-dim)]">{p.desc}</div>
			</button>
		{/each}
	</div>

	{#if a}
		{#if stale}
			<div class="rounded-xl border border-[var(--color-warn)] bg-amber-500/10 p-3 text-sm">
				⚠️ Data asumsi ini berumur lebih dari 6 bulan (per {dateID(a.as_of)}). Sebaiknya dicek
				ulang.
			</div>
		{/if}
		<div class="card overflow-hidden">
			<table class="w-full text-sm">
				<thead class="bg-[var(--color-void-2)] text-xs text-[var(--color-ink-dim)]">
					<tr>
						<th class="px-4 py-2 text-left font-medium">Parameter</th>
						<th class="px-4 py-2 text-right font-medium">Nilai</th>
						<th class="px-4 py-2 text-left font-medium">Sumber</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-[var(--color-line)]">
					<tr>
						<td class="px-4 py-2.5">Inflasi</td>
						<td class="num px-4 py-2.5 text-right font-semibold"
							>{percent(a.values.inflation)}/th</td
						>
						<td class="px-4 py-2.5 text-xs text-[var(--color-ink-dim)]">
							<a
								href={a.sources.inflation?.url}
								target="_blank"
								rel="noreferrer"
								class="underline hover:text-[var(--color-accent)]"
								>{a.sources.inflation?.label ?? 'Asumsi'}</a
							>
						</td>
					</tr>
					{#each Object.entries(a.values.returns) as [k, v]}
						<tr>
							<td class="px-4 py-2.5 capitalize">{k.replace('_', ' ')}</td>
							<td class="num px-4 py-2.5 text-right">{percent(v as number)}/th</td>
							<td class="px-4 py-2.5 text-xs text-[var(--color-ink-dim)]">
								{#if a.sources[`returns.${k}`]}
									<a
										href={a.sources[`returns.${k}`].url}
										target="_blank"
										rel="noreferrer"
										class="underline hover:text-[var(--color-accent)]"
										>{a.sources[`returns.${k}`].label}</a
									>
								{/if}
							</td>
						</tr>
					{/each}
					<tr>
						<td class="px-4 py-2.5">Kenaikan gaji</td>
						<td class="num px-4 py-2.5 text-right">{percent(a.values.salary_growth)}/th</td>
						<td class="px-4 py-2.5 text-xs text-[var(--color-ink-dim)]"
							>{a.sources.salary_growth?.label}</td
						>
					</tr>
					<tr>
						<td class="px-4 py-2.5">Premi gaji S2</td>
						<td class="num px-4 py-2.5 text-right">{percent(a.values.s2_salary_premium)}</td>
						<td class="px-4 py-2.5 text-xs text-[var(--color-ink-dim)]"
							>{a.sources.s2_salary_premium?.label}</td
						>
					</tr>
					<tr class="bg-[var(--color-void-2)]">
						<td class="px-4 py-2.5 font-medium">Batas bunga pinjol</td>
						<td class="px-4 py-2.5 text-xs">
							{a.regulatory.consumer_caps
								.map(
									(c) =>
										`${((c.rate_daily_max ?? 0) * 100).toFixed(1)}%/hari ${c.tenor_max_months ? '≤' + c.tenor_max_months + ' bln' : '>' + a.regulatory.consumer_caps[0].tenor_max_months + ' bln'}`
								)
								.join(' · ')}
						</td>
						<td class="px-4 py-2.5 text-xs text-[var(--color-ink-dim)]">
							<Tooltip text={a.sources.regulatory?.label ?? ''}>
								<a
									href={a.sources.regulatory?.url}
									target="_blank"
									rel="noreferrer"
									class="underline hover:text-[var(--color-accent)]">{a.regulatory.version}</a
								>
							</Tooltip>
						</td>
					</tr>
					<tr>
						<td class="px-4 py-2.5">Batas rasio cicilan (DSR)</td>
						<td class="num px-4 py-2.5 text-right">{percent(a.regulatory.dsr_cap, 0)}</td>
						<td class="px-4 py-2.5 text-xs text-[var(--color-ink-dim)]">sejak 2026</td>
					</tr>
					<tr>
						<td class="px-4 py-2.5">Lock cap bunga + denda</td>
						<td class="num px-4 py-2.5 text-right"
							>{percent(a.regulatory.lock_cap_ratio, 0)} pokok</td
						>
						<td class="px-4 py-2.5 text-xs text-[var(--color-ink-dim)]">maksimal 100% pokok</td>
					</tr>
				</tbody>
			</table>
		</div>
		<p class="text-xs text-[var(--color-ink-dim)]">
			Data per <strong class="text-[var(--color-ink)]">{dateID(a.as_of)}</strong> · set
			<code>{a.code}</code>
		</p>
	{/if}
</div>
