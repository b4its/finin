<script lang="ts">
	import BranchTree from '$lib/components/multiverse/BranchTree.svelte';
	import NetWorthChart from '$lib/components/multiverse/NetWorthChart.svelte';
	import TimeScrubber from '$lib/components/multiverse/TimeScrubber.svelte';
	import TwinCard from '$lib/components/multiverse/TwinCard.svelte';
	import CompareView from '$lib/components/multiverse/CompareView.svelte';
	import StressTestPanel from '$lib/components/multiverse/StressTestPanel.svelte';
	import RobustBadge from '$lib/components/multiverse/RobustBadge.svelte';
	import AssumptionPanel from '$lib/components/multiverse/AssumptionPanel.svelte';
	import RecommendationPanel from '$lib/components/multiverse/RecommendationPanel.svelte';
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Modal from '$lib/components/ui/Modal.svelte';
	import { sim } from '$lib/stores/simulation.svelte';
	import type { Twin } from '$lib/api/types';
	import { api } from '$lib/api/client';
	import { rupiahBrief, months, percent } from '$lib/utils/format';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';

	let simId = $derived($page.params.id ?? '');

	let year = $state(10);
	let real = $state(false);
	let detailTwin = $state<Twin | null>(null);
	let detailOpen = $state(false);
	let preset = $state<string | null>(null);

	onMount(async () => {
		if (!sim.result || sim.result.id !== simId) {
			try {
				sim.result = await api.getSimulation(simId);
				sim.input.preset = sim.result.preset;
				api
					.recommendation(simId)
					.then((r) => (sim.recommendation = r))
					.catch(() => {});
			} catch (e) {
				sim.errorMsg = String(e);
			}
		}
		if (sim.result) preset = sim.result.preset;
	});

	let result = $derived(sim.result);
	let bestCode = $derived(sim.recommendation?.best_twin ?? null);

	function openDetail(t: Twin) {
		detailTwin = t;
		detailOpen = true;
	}

	async function changePreset(p: string) {
		preset = p;
		await sim.recompute(p);
	}

	const presetLabels: Record<string, string> = {
		konservatif: 'Konservatif',
		moderat: 'Moderat',
		optimis: 'Optimis'
	};
</script>

<svelte:head><title>Multiverse — Financial Twin</title></svelte:head>

<div class="mx-auto max-w-6xl px-5 py-6">
	<header class="mb-6 flex flex-wrap items-center justify-between gap-3">
		<a href="/" class="flex items-center gap-2 font-bold"><span>🌌</span> Financial Twin</a>
		<div class="flex flex-wrap items-center gap-2">
			{#if result}<RobustBadge
					robust={result.robust}
					reason={result.robust_reason}
					winners={result.preset_winners}
				/>{/if}
			<a href="/start" class="btn btn-ghost !py-1.5">Simulasi baru</a>
		</div>
	</header>

	{#if sim.errorMsg}
		<div class="rounded-xl border border-[var(--color-danger)] bg-red-500/10 p-4 text-sm">
			{sim.errorMsg}
		</div>
	{:else if !result}
		<div class="flex items-center gap-3 p-8 text-[var(--color-ink-dim)]">
			<span class="animate-pulse text-xl">✨</span> Memuat multiverse…
		</div>
	{:else}
		<section class="mb-5">
			<h1 class="text-2xl font-bold">Multiverse-mu, {result.twins.length} cabang</h1>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Set asumsi {result.assumption_code} · engine {result.engine_version} · preset
				<strong class="text-[var(--color-ink)]"
					>{presetLabels[result.preset] ?? result.preset}</strong
				>
			</p>
		</section>

		{#if result.flags.length}
			<section class="mb-5 space-y-2">
				{#each result.flags as f (f.code)}
					<div
						class="flex items-start gap-3 rounded-xl border p-3 text-sm"
						class:alert-red={f.level === 'red'}
						class:alert-warn={f.level === 'orange'}
					>
						<Badge level={f.level}>{f.level === 'red' ? 'Bendera OJK' : 'Perhatian'}</Badge>
						<p class="flex-1 text-[var(--color-ink-dim)]">{f.msg}</p>
					</div>
				{/each}
			</section>
		{/if}

		<div class="grid grid-cols-1 gap-5 lg:grid-cols-3">
			<div class="space-y-5 lg:col-span-2">
				<BranchTree twins={result.twins} selectedYear={year} />
				<TimeScrubber bind:year narration={sim.textForTwin(result.twins[1]?.code ?? '0', year)} />
				<NetWorthChart twins={result.twins} bind:selectedYear={year} bind:real />
				<CompareView twins={result.twins} />
				<StressTestPanel twins={result.twins} />
			</div>

			<div class="space-y-4">
				<div class="card p-4">
					<div class="mb-3 flex items-center justify-between">
						<h3 class="text-sm font-semibold">Preset asumsi</h3>
						{#if result.robust}<span class="text-xs text-[var(--color-ok)]">robust</span>{/if}
					</div>
					<div class="flex flex-wrap gap-1.5">
						{#each Object.entries(presetLabels) as [k, l]}
							<button class="chip" class:active={preset === k} onclick={() => changePreset(k)}>
								{l}
							</button>
						{/each}
					</div>
					<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
						Mengubah preset akan menghitung ulang semua twin.
					</p>
				</div>

				{#each result.twins as t (t.code)}
					<TwinCard
						twin={t}
						{year}
						narrative={sim.textForTwin(t.code, year)}
						isBest={t.code === bestCode}
						onSelect={openDetail}
					/>
				{/each}

				<RecommendationPanel
					recommendation={sim.recommendation}
					twins={result.twins}
					simulationId={result.id}
				/>

				<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4">
					<p class="text-xs text-[var(--color-ink-dim)]">Bagikan hasil ini</p>
					<button
						class="btn btn-ghost mt-2 w-full !text-xs"
						onclick={() => navigator.clipboard?.writeText(window.location.href)}
					>
						Salin link simulasi
					</button>
				</div>
			</div>
		</div>

		<div class="mt-6">
			<AssumptionPanel assumptions={result.assumptions} />
		</div>
	{/if}

	<div class="mt-8">
		<Disclaimer />
	</div>
</div>

<Modal
	bind:open={detailOpen}
	title={detailTwin ? `${detailTwin.label} — Twin ${detailTwin.code}` : ''}
>
	{#if detailTwin}
		<p class="mb-4 text-sm text-[var(--color-ink-dim)]">{detailTwin.description}</p>
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Net worth th {year}</div>
				<div class="num text-lg font-bold">
					{rupiahBrief(detailTwin.yearly_series.find((p) => p.year === year)?.net_worth ?? 0)}
				</div>
			</div>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Nilai riil</div>
				<div class="num text-lg font-bold">
					{rupiahBrief(detailTwin.yearly_series.find((p) => p.year === year)?.net_worth_real ?? 0)}
				</div>
			</div>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Dana darurat</div>
				<div class="num text-lg font-bold">
					{months(detailTwin.yearly_series.find((p) => p.year === year)?.emergency_months ?? 0)}
				</div>
			</div>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">DSR</div>
				<div class="num text-lg font-bold">
					{percent(detailTwin.yearly_series.find((p) => p.year === year)?.dsr ?? 0, 0)}
				</div>
			</div>
		</div>

		{#if detailTwin.flags.length}
			<div class="mt-4 space-y-2">
				{#each detailTwin.flags as f (f.code)}
					<div class="rounded-xl border border-[var(--color-line)] p-3 text-xs">
						<Badge level={f.level}>{f.level}</Badge>
						<span class="ml-2 text-[var(--color-ink-dim)]">{f.msg}</span>
					</div>
				{/each}
			</div>
		{/if}

		<div class="mt-4">
			<h4 class="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
				Stress test
			</h4>
			<div class="space-y-1.5">
				{#each detailTwin.stress as s}
					<div class="flex items-center justify-between text-sm">
						<span class="text-[var(--color-ink-dim)]">{s.label}</span>
						<Badge level={s.survived ? 'ok' : 'red'}
							>{s.survived ? 'Bertahan' : 'Tidak bertahan'}</Badge
						>
					</div>
				{/each}
			</div>
		</div>

		<div class="mt-4">
			<h4 class="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
				Narasi
			</h4>
			<div class="space-y-2">
				{#each [5, 10, 20] as h}
					{#if sim.textForTwin(detailTwin.code, h)}
						<p
							class="rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-2.5 text-xs leading-relaxed"
						>
							{sim.textForTwin(detailTwin.code, h)}
						</p>
					{/if}
				{/each}
			</div>
		</div>
	{/if}
</Modal>
