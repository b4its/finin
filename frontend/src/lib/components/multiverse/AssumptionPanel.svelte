<script lang="ts">
	import { api } from '$lib/api/client';
	import type { AssumptionsSnapshot } from '$lib/api/types';
	import { percent, dateID, isStale } from '$lib/utils/format';

	let { assumptions }: { assumptions: AssumptionsSnapshot } = $props();
	let open = $state(false);
	let fresh = $state<AssumptionsSnapshot | null>(null);

	let current = $derived(fresh ?? assumptions);
	let stale = $derived(isStale(current.as_of));

	async function toggle() {
		open = !open;
		if (open && !fresh) {
			try {
				fresh = await api.assumptions(current.preset);
			} catch {
				/* biarkan pakai yang ada */
			}
		}
	}

	const presets = [
		{ key: 'konservatif', label: 'Konservatif' },
		{ key: 'moderat', label: 'Moderat' },
		{ key: 'optimis', label: 'Optimis' }
	];
</script>

<div class="card overflow-hidden">
	<button class="flex w-full items-center justify-between p-4 text-left" onclick={toggle}>
		<div>
			<div class="text-sm font-semibold">Asumsi & sumber</div>
			<div class="text-xs text-[var(--color-ink-dim)]">
				Set {current.code} · data per {dateID(current.as_of)}
			</div>
		</div>
		<span class="text-[var(--color-ink-dim)]">{open ? '▲' : '▼'}</span>
	</button>

	{#if open}
		<div class="border-t border-[var(--color-line)] p-4">
			{#if stale}
				<div class="mb-3 rounded-xl border border-[var(--color-warn)] bg-amber-500/10 p-3 text-xs">
					⚠️ Data ini berumur lebih dari 6 bulan. Periksa kesegaran sumber sebelum mengambil
					keputusan.
				</div>
			{/if}

			<h4 class="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
				Parameter terpakai
			</h4>
			<div class="grid grid-cols-1 gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
				{#each Object.entries(current.values) as [k, v]}
					{#if typeof v === 'number'}
						<div class="flex justify-between border-b border-[var(--color-line)] py-1.5">
							<span class="capitalize text-[var(--color-ink-dim)]">{k.replace('_', ' ')}</span>
							<span class="num font-medium">{percent(v)}</span>
						</div>
					{:else if k === 'returns' && typeof v === 'object'}
						{#each Object.entries(v as Record<string, number>) as [rk, rv]}
							<div class="flex justify-between border-b border-[var(--color-line)] py-1.5">
								<span class="text-[var(--color-ink-dim)]">imbal {rk.replace('_', ' ')}</span>
								<span class="num font-medium">{percent(rv)}</span>
							</div>
						{/each}
					{/if}
				{/each}
			</div>

			<h4
				class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]"
			>
				Regulasi OJK ({current.regulatory.version})
			</h4>
			<div
				class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3 text-xs"
			>
				<p>
					Mencabut: {current.regulatory.replaces} · berlaku {dateID(
						current.regulatory.effective_from
					)}
				</p>
				<ul class="mt-2 space-y-1">
					{#each current.regulatory.consumer_caps as c}
						<li>
							Bunga maks {percent(c.rate_daily_max, 2)}/hari untuk tenor
							{c.tenor_max_months
								? `≤ ${c.tenor_max_months} bulan`
								: `> ${current.regulatory.consumer_caps[0].tenor_max_months} bulan`}
							(denda sama).
						</li>
					{/each}
					<li>Lock cap: bunga + denda ≤ {percent(current.regulatory.lock_cap_ratio, 0)} pokok.</li>
					<li>
						Batas rasio cicilan: {percent(current.regulatory.dsr_cap, 0)} penghasilan (sejak 2026).
					</li>
					<li>Macet (TWP90): tunggakan &gt; {current.regulatory.default_days} hari.</li>
				</ul>
			</div>

			<h4
				class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]"
			>
				Sumber
			</h4>
			<ul class="space-y-1.5 text-xs">
				{#each Object.entries(current.sources) as [k, s]}
					<li class="flex flex-wrap items-baseline gap-1.5">
						<span class="font-medium text-[var(--color-ink)]">{k}:</span>
						{#if s.url}
							<a
								href={s.url}
								target="_blank"
								rel="noreferrer"
								class="text-[var(--color-accent)] underline">{s.label}</a
							>
						{:else}
							<span class="text-[var(--color-ink-dim)]">{s.label}</span>
						{/if}
						<span class="chip !py-0 !text-[0.6rem] text-[var(--color-ink-dim)]"
							>{dateID(s.as_of)}</span
						>
						{#if s.kind === 'assumption'}
							<span class="chip !py-0 !text-[0.6rem] border-amber-500/40 text-[var(--color-warn)]"
								>asumsi</span
							>
						{/if}
					</li>
				{/each}
			</ul>

			{#if current.market_context?.length}
				<h4
					class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]"
				>
					Konteks pasar (data masalah)
				</h4>
				<ul class="space-y-1 text-xs text-[var(--color-ink-dim)]">
					{#each current.market_context as m}
						<li>• {m.label} <span class="opacity-70">— {m.source}</span></li>
					{/each}
				</ul>
			{/if}

			<h4
				class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]"
			>
				Preset sensitivitas
			</h4>
			<div class="overflow-x-auto">
				<table class="w-full text-xs">
					<thead class="text-[var(--color-ink-dim)]">
						<tr>
							<th class="px-2 py-1 text-left font-medium">Parameter</th>
							{#each presets as p}<th class="px-2 py-1 text-right font-medium">{p.label}</th>{/each}
						</tr>
					</thead>
					<tbody class="num">
						<tr>
							<td class="px-2 py-1 family-sans">Inflasi</td>
							{#each presets as p}<td class="px-2 py-1 text-right"
									>{percent((current.presets[p.key]?.inflation as number) ?? 0)}</td
								>{/each}
						</tr>
						<tr>
							<td class="px-2 py-1">Kenaikan gaji</td>
							{#each presets as p}<td class="px-2 py-1 text-right"
									>{percent((current.presets[p.key]?.salary_growth as number) ?? 0)}</td
								>{/each}
						</tr>
						<tr>
							<td class="px-2 py-1">Premi S2</td>
							{#each presets as p}<td class="px-2 py-1 text-right"
									>{percent((current.presets[p.key]?.s2_salary_premium as number) ?? 0)}</td
								>{/each}
						</tr>
						<tr>
							<td class="px-2 py-1">Pasar uang</td>
							{#each presets as p}<td class="px-2 py-1 text-right"
									>{percent(
										(current.presets[p.key]?.returns as Record<string, number>)?.money_market ?? 0
									)}</td
								>{/each}
						</tr>
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>
