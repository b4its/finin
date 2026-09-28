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
	import ReportModal from '$lib/components/multiverse/ReportModal.svelte';
	import PitchModal from '$lib/components/multiverse/PitchModal.svelte';
	import MilestoneTracker from '$lib/components/multiverse/MilestoneTracker.svelte';
	import FinancialHealthScorecard from '$lib/components/multiverse/FinancialHealthScorecard.svelte';
	import PurchasingPowerHorizon from '$lib/components/multiverse/PurchasingPowerHorizon.svelte';
	import PortfolioAllocationRadar from '$lib/components/multiverse/PortfolioAllocationRadar.svelte';
	import TaxAndBPJSBreakdown from '$lib/components/multiverse/TaxAndBPJSBreakdown.svelte';
	import ZakatAndFinalTaxCalculator from '$lib/components/multiverse/ZakatAndFinalTaxCalculator.svelte';
	import PensionAndFireCalculator from '$lib/components/multiverse/PensionAndFireCalculator.svelte';
	import SandwichGenerationCalculator from '$lib/components/multiverse/SandwichGenerationCalculator.svelte';
	import EstatePlanningSimulator from '$lib/components/multiverse/EstatePlanningSimulator.svelte';
	import MonteCarloSimulation from '$lib/components/multiverse/MonteCarloSimulation.svelte';
	import DebtPayoffAccelerator from '$lib/components/multiverse/DebtPayoffAccelerator.svelte';
	import EducationFundPlanner from '$lib/components/multiverse/EducationFundPlanner.svelte';
	import EmergencyRunwaySimulator from '$lib/components/multiverse/EmergencyRunwaySimulator.svelte';
	import FinancialGoalPlanner from '$lib/components/multiverse/FinancialGoalPlanner.svelte';
	import ScenarioSandbox from '$lib/components/multiverse/ScenarioSandbox.svelte';
	import ShareModal from '$lib/components/multiverse/ShareModal.svelte';
	import CommandPalette from '$lib/components/multiverse/CommandPalette.svelte';
	import ExecutiveSummary from '$lib/components/multiverse/ExecutiveSummary.svelte';
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Modal from '$lib/components/ui/Modal.svelte';
	import Dropdown from '$lib/components/ui/Dropdown.svelte';
	import { sim } from '$lib/stores/simulation.svelte';
	import { toast } from '$lib/stores/toast.svelte';
	import type { Twin } from '$lib/api/types';
	import { api } from '$lib/api/client';
	import { rupiahBrief, months, percent } from '$lib/utils/format';
	import { page } from '$app/state';
	import { replaceState, afterNavigate } from '$app/navigation';
	import { untrack } from 'svelte';

	let simId = $derived(page.params.id ?? '');
	let year = $state(10);
	let real = $state(false);
	let detailTwin = $state<Twin | null>(null);
	let detailOpen = $state(false);
	let preset = $state<string | null>(null);
	let activeShock = $state<string | null>(null);
	let assumptionOverrides = $state<Record<string, unknown>>({});
	let focusedTwin = $state<string | null>(null);
	let reportOpen = $state(false);
	let pitchOpen = $state(false);
	let shareOpen = $state(false);
	const VALID_TABS = ['overview', 'risk', 'strategy', 'future', 'all'] as const;
	type TabId = (typeof VALID_TABS)[number];

	function hashTab(raw: string): TabId {
		const id = (raw ?? '').replace('#', '') as TabId;
		return VALID_TABS.includes(id) ? id : 'overview';
	}

	let activeTab = $state<TabId>('overview');

	/** Pilih tab: perbarui state + hash URL agar bisa dibagikan/di-bookmark. */
	function selectTab(id: TabId, focus = false) {
		activeTab = id;
		replaceState(`#${id}`, { tab: id });
		if (focus) {
			queueMicrotask(() => document.getElementById(`tab-${id}`)?.focus());
		}
	}

	// Daftar modul per tab — satu sumber kebenaran agar jumlah modul akurat
	// dan tidak lagi hard-coded (menghindari hitungan yang meleset).
	const TAB_MODULES = {
		overview: ['BranchTree', 'TimeScrubber', 'NetWorthChart', 'CompareView', 'MilestoneTracker'],
		risk: ['MonteCarlo', 'HealthScorecard', 'EmergencyRunway', 'StressTest', 'PurchasingPower'],
		strategy: ['GoalPlanner', 'DebtPayoff', 'EducationFund', 'PortfolioRadar', 'ScenarioSandbox'],
		future: ['PensionFIRE', 'SandwichGen', 'EstatePlanning', 'ZakatTax', 'TaxBPJS']
	} as const;

	const TABS = [
		{
			id: 'overview',
			label: 'Multiverse Utama',
			icon: '🌌',
			count: TAB_MODULES.overview.length
		},
		{ id: 'risk', label: 'Risiko & Ketahanan', icon: '🎲', count: TAB_MODULES.risk.length },
		{
			id: 'strategy',
			label: 'Akselerasi & Target',
			icon: '🎯',
			count: TAB_MODULES.strategy.length
		},
		{
			id: 'future',
			label: 'Pensiun, Waris & Pajak',
			icon: '🏛️',
			count: TAB_MODULES.future.length
		},
		{ id: 'all', label: 'Semua Modul', icon: '📋', count: Object.values(TAB_MODULES).flat().length }
	] as const;

	/**
	 * Muat simulasi secara reaktif terhadap `simId`. Sebelumnya memakai onMount
	 * sehingga navigasi klien dari /sim/A -> /sim/B tidak memuat ulang data.
	 * Efek ini membersihkan state lama sebelum memuat id baru.
	 */
	$effect(() => {
		const id = simId;
		if (!id) return;
		const current = untrack(() => sim.result);
		if (current?.id === id) {
			preset = current.preset;
			return;
		}
		let cancelled = false;
		sim.errorMsg = null;
		sim.result = null;
		sim.recommendation = null;
		api
			.getSimulation(id)
			.then((res) => {
				if (cancelled) return;
				sim.result = res;
				sim.input.preset = res.preset;
				preset = res.preset;
				api
					.recommendation(id)
					.then((r) => {
						if (!cancelled) sim.recommendation = r;
					})
					.catch(() => {});
			})
			.catch((e) => {
				if (!cancelled) sim.errorMsg = String(e);
			});
		return () => {
			cancelled = true;
		};
	});

	// Sinkronkan tab aktif dari hash URL saat dimuat, melalui tautan langsung,
	// dan pada navigasi back/forward. `afterNavigate` sudah mencakup popstate,
	// sehingga listener popstate manual tidak lagi diperlukan (menghindari double-fire).
	afterNavigate(() => {
		activeTab = hashTab(window.location.hash);
	});

	let result = $derived(sim.result);
	let bestCode = $derived(sim.recommendation?.best_twin ?? sim.result?.best_twin ?? null);

	function openDetail(t: Twin) {
		detailTwin = t;
		detailOpen = true;
	}

	async function changePreset(p: string) {
		preset = p;
		await sim.recompute(p);
		if (sim.errorMsg) {
			toast.error('Gagal menghitung ulang dengan preset baru.');
		} else {
			toast.success(`Preset diubah ke ${presetLabels[p] ?? p} — semua twin dihitung ulang.`);
		}
	}

	const presetLabels: Record<string, string> = {
		konservatif: 'Konservatif',
		moderat: 'Moderat',
		optimis: 'Optimis'
	};

	// Bobot komponen skor (PRD §8) + label manusiawi.
	const scoreLabel: Record<string, string> = {
		net_worth_real: 'Net worth riil th-10',
		emergency: 'Dana darurat',
		dsr: 'Rasio cicilan (DSR)',
		stress: 'Lolos stress test',
		robust: 'Konsisten antar preset'
	};
	const scoreWeight: Record<string, number> = {
		net_worth_real: 0.3,
		emergency: 0.25,
		dsr: 0.2,
		stress: 0.15,
		robust: 0.1
	};
	function weightOf(k: string): number {
		return scoreWeight[k] ?? 0.1;
	}

	/** Navigasi tablist dengan panah kiri/kanan (pola WAI-ARIA). */
	function onTabKey(e: KeyboardEvent, idx: number) {
		const last = TABS.length - 1;
		let next = idx;
		if (e.key === 'ArrowRight') next = idx === last ? 0 : idx + 1;
		else if (e.key === 'ArrowLeft') next = idx === 0 ? last : idx - 1;
		else if (e.key === 'Home') next = 0;
		else if (e.key === 'End') next = last;
		else return;
		e.preventDefault();
		selectTab(TABS[next].id as TabId, true);
	}
</script>

<svelte:head><title>Multiverse — Financial Twin</title></svelte:head>

<div class="mx-auto max-w-6xl px-4 py-5 sm:px-5 sm:py-6">
	<header class="mb-5 flex flex-wrap items-center justify-between gap-3">
		<p class="text-sm font-semibold text-[var(--color-ink-dim)]">Multiverse hub</p>
		<div class="flex flex-wrap items-center gap-2">
			{#if result}
				<CommandPalette
					tabs={TABS}
					twins={result.twins}
					simulationId={result.id}
					onSelectTab={(id) => selectTab(id as TabId)}
					onSelectTwin={(code) => {
						const t = result?.twins.find((x) => x.code === code);
						if (t) openDetail(t);
					}}
					onOpenReport={() => (reportOpen = true)}
					onOpenPitch={() => (pitchOpen = true)}
					onOpenShare={() => (shareOpen = true)}
				/>
				<RobustBadge
					robust={result.robust}
					reason={result.robust_reason}
					winners={result.preset_winners}
					drivers={result.sensitivity_drivers}
				/>
				<button
					class="btn btn-ghost !py-1.5 !px-3 text-xs"
					onclick={() => (reportOpen = true)}
					title="Cetak atau unduh laporan PDF eksekutif"
				>
					📄 Laporan PDF
				</button>
				<button
					class="btn btn-ghost !py-1.5 !px-3 text-xs font-semibold text-[var(--color-accent)]"
					onclick={() => (pitchOpen = true)}
					title="Mode presentasi cepat untuk juri"
				>
					⚡ Presentasi Juri
				</button>
				<button
					class="btn btn-ghost !py-1.5 !px-3 text-xs font-semibold text-sky-400"
					onclick={() => (shareOpen = true)}
					title="Bagikan kartu persona dan hasil simulasi ke WhatsApp / medsos"
				>
					✨ Bagikan Hasil
				</button>
				<Dropdown label="📥 Unduh Data ▾" title="Unduh data simulasi lengkap (CSV atau JSON)">
					<a
						href={api.exportCsvUrl(result.id)}
						class="block rounded-lg px-3 py-2 text-xs font-medium text-[var(--color-ink)] hover:bg-[var(--color-void-3)]"
						download
					>
						📊 CSV Trajektori 240 Bulan
					</a>
					<a
						href={api.exportJsonUrl(result.id)}
						class="block rounded-lg px-3 py-2 text-xs font-medium text-[var(--color-ink)] hover:bg-[var(--color-void-3)]"
						download
					>
						💾 JSON Paket Simulasi
					</a>
				</Dropdown>
				<a
					href={`/bandingkan?ids=${result.id}`}
					class="btn btn-ghost !py-1.5 !px-3 text-xs"
					title="Bandingkan simulasi ini dengan simulasi lain di riwayatmu"
				>
					⚖️ Bandingkan
				</a>
			{/if}
			<a href="/start" class="btn btn-ghost !py-1.5">Simulasi baru</a>
		</div>
	</header>

	{#if sim.errorMsg}
		<div class="card p-8 text-center">
			<p class="text-4xl" aria-hidden="true">🛰️</p>
			<h2 class="mt-3 text-lg font-bold">Multiverse tidak dapat dimuat</h2>
			<p class="mx-auto mt-1 max-w-md text-sm text-[var(--color-ink-dim)]">
				Simulasi tidak ditemukan, sudah kedaluwarsa, atau backend sedang tidak dapat dijangkau.
			</p>
			<code
				class="mx-auto mt-3 block max-w-md truncate rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] px-3 py-2 text-xs text-[var(--color-ink-dim)]"
				title={sim.errorMsg}>{sim.errorMsg}</code
			>
			<div class="mt-5 flex justify-center gap-2">
				<a href="/start" class="btn btn-primary">Buat simulasi baru</a>
				<a href="/saya" class="btn btn-ghost">Riwayat simulasi</a>
			</div>
		</div>
	{:else if !result}
		<div class="grid grid-cols-1 gap-5 lg:grid-cols-3" aria-busy="true" aria-live="polite">
			<div class="space-y-5 lg:col-span-2">
				<div class="card h-64 skeleton"></div>
				<div class="card h-40 skeleton"></div>
			</div>
			<div class="space-y-4">
				{#each Array(3) as _}
					<div class="card h-32 skeleton"></div>
				{/each}
			</div>
			<span class="sr-only">Memuat multiverse…</span>
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

		<div class="mb-5">
			<ExecutiveSummary
				twins={result.twins}
				recommendation={sim.recommendation}
				robust={result.robust}
				robustReason={result.robust_reason}
				{year}
				flagsCount={result.flags.length}
				onOpenTwin={(code) => {
					const t = result?.twins.find((x) => x.code === code);
					if (t) openDetail(t);
				}}
			/>
		</div>

		<!-- Multiverse Hub Navigation Bar -->
		<div
			class="no-print sticky top-14 z-30 mb-5 flex flex-wrap items-center gap-1.5 rounded-2xl border border-[var(--color-line)] bg-[var(--color-void-2)]/95 p-1.5 shadow-sm backdrop-blur-md"
			role="tablist"
			aria-label="Modul analisis multiverse"
		>
			{#each TABS as tab, i (tab.id)}
				<button
					type="button"
					role="tab"
					id="tab-{tab.id}"
					aria-selected={activeTab === tab.id}
					aria-controls="panel-{tab.id}"
					tabindex={activeTab === tab.id ? 0 : -1}
					class="flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition-all {activeTab ===
					tab.id
						? 'bg-[var(--color-accent)] font-bold text-slate-950 shadow-md'
						: 'text-[var(--color-ink-dim)] hover:bg-[var(--color-void-3)] hover:text-[var(--color-ink)]'}"
					onclick={() => selectTab(tab.id as TabId)}
					onkeydown={(e) => onTabKey(e, i)}
				>
					<span aria-hidden="true">{tab.icon}</span>
					<span>{tab.label}</span>
					<span
						class="rounded-full px-1.5 py-0.5 text-[10px] {activeTab === tab.id
							? 'bg-slate-900/30 font-black text-slate-950'
							: 'bg-[var(--color-void-1)] text-[var(--color-ink-dim)]'}"
					>
						{tab.count}
					</span>
				</button>
			{/each}
		</div>

		<div class="grid grid-cols-1 gap-5 lg:grid-cols-3">
			<div
				class="space-y-5 lg:col-span-2"
				id="panel-{activeTab}"
				role="tabpanel"
				aria-labelledby="tab-{activeTab}"
				tabindex="0"
			>
				{#if activeTab === 'overview' || activeTab === 'all'}
					<BranchTree twins={result.twins} selectedYear={year} brokenShock={activeShock} />
					<TimeScrubber
						bind:year
						twins={result.twins}
						narration={sim.textForTwin(focusedTwin ?? result.twins[1]?.code ?? '0', year)}
						onFocusTwin={(c) => (focusedTwin = c)}
					/>
					<NetWorthChart twins={result.twins} bind:selectedYear={year} bind:real />
					<CompareView twins={result.twins} {year} />
					<MilestoneTracker twins={result.twins} />
				{/if}

				{#if activeTab === 'risk' || activeTab === 'all'}
					<MonteCarloSimulation twins={result.twins} {simId} preset={preset ?? result.preset} />
					<FinancialHealthScorecard twins={result.twins} />
					<EmergencyRunwaySimulator twins={result.twins} profile={sim.input.profile} />
					<StressTestPanel twins={result.twins} bind:active={activeShock} />
					<PurchasingPowerHorizon twins={result.twins} />
				{/if}

				{#if activeTab === 'strategy' || activeTab === 'all'}
					<FinancialGoalPlanner twins={result.twins} profile={sim.input.profile} />
					<DebtPayoffAccelerator profile={sim.input.profile} twins={result.twins} />
					<EducationFundPlanner twins={result.twins} profile={sim.input.profile} />
					<PortfolioAllocationRadar twins={result.twins} />
					<ScenarioSandbox
						baseExpense={sim.input.profile.expense_monthly || 5_000_000}
						baseIncome={sim.input.profile.income_monthly || 0}
					/>
				{/if}

				{#if activeTab === 'future' || activeTab === 'all'}
					<PensionAndFireCalculator twins={result.twins} profile={sim.input.profile} />
					<SandwichGenerationCalculator profile={sim.input.profile} twins={result.twins} />
					<EstatePlanningSimulator twins={result.twins} profile={sim.input.profile} />
					<ZakatAndFinalTaxCalculator twins={result.twins} profile={sim.input.profile} />
					<TaxAndBPJSBreakdown initialGross={sim.input.profile.income_monthly || 10000000} />
				{/if}
			</div>

			<div class="space-y-4">
				<div class="card p-4">
					<div class="mb-3 flex items-center justify-between">
						<h3 class="text-sm font-semibold">Preset asumsi</h3>
						{#if result.robust}<span class="text-xs text-[var(--color-ok)]">robust</span>{/if}
					</div>
					<div class="flex flex-wrap gap-1.5">
						{#each Object.entries(presetLabels) as [k, l]}
							<button
								class="chip"
								class:active={preset === k}
								disabled={sim.loading}
								onclick={() => changePreset(k)}
							>
								{l}
							</button>
						{/each}
					</div>
					<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
						Mengubah preset akan menghitung ulang semua twin.
					</p>
				</div>

				{#if sim.narrating}
					<div
						class="flex items-center gap-2 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] px-3 py-2 text-xs text-[var(--color-ink-dim)]"
						aria-live="polite"
					>
						<span
							class="inline-block h-3 w-3 shrink-0 animate-spin rounded-full border-2 border-[var(--color-accent)] border-t-transparent"
						></span>
						Menulis narasi per horizon (5/10/20 tahun)…
					</div>
				{/if}

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
					<div class="flex items-center justify-between">
						<p class="text-xs font-semibold text-[var(--color-ink)]">Bagikan Hasil Multiverse</p>
						<span class="text-xs">✨</span>
					</div>
					<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
						Unduh kartu persona digital atau bagikan proyeksi ke WhatsApp & X.
					</p>
					<button
						class="btn btn-primary mt-3 w-full !text-xs font-semibold"
						onclick={() => (shareOpen = true)}
					>
						✨ Buka Menu Berbagi & Kartu Persona
					</button>
					<button
						class="btn btn-ghost mt-1.5 w-full !text-xs text-[var(--color-ink-dim)]"
						onclick={async () => {
							try {
								await navigator.clipboard?.writeText(window.location.href);
								toast.success('Link simulasi disalin ke clipboard');
							} catch {
								toast.error('Gagal menyalin link — salin manual dari address bar');
							}
						}}
					>
						Salin link URL
					</button>
				</div>
			</div>
		</div>

		<div class="mt-6">
			<AssumptionPanel
				assumptions={result.assumptions}
				bind:overrides={assumptionOverrides}
				onRecompute={(ov) => sim.recompute(preset ?? result.preset, ov)}
			/>
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
		{@const pt = detailTwin.yearly_series.find((p) => p.year === year)}
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Net worth th {year}</div>
				<div class="num text-lg font-bold">{rupiahBrief(pt?.net_worth ?? 0)}</div>
			</div>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Nilai riil</div>
				<div class="num text-lg font-bold">{rupiahBrief(pt?.net_worth_real ?? 0)}</div>
			</div>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Dana darurat</div>
				<div class="num text-lg font-bold">{months(pt?.emergency_months ?? 0)}</div>
			</div>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">DSR</div>
				<div class="num text-lg font-bold">{percent(pt?.dsr ?? 0, 0)}</div>
			</div>
		</div>

		<!-- Aset, utang, arus kas (field yang sebelumnya tidak ditampilkan) -->
		<div
			class="mt-3 grid grid-cols-2 gap-4 rounded-xl border border-[var(--color-line)] p-3 sm:grid-cols-4"
		>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Kas</div>
				<div class="num font-semibold">{rupiahBrief(pt?.cash ?? 0)}</div>
			</div>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Investasi</div>
				<div class="num font-semibold">{rupiahBrief(pt?.invest ?? 0)}</div>
			</div>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Utang</div>
				<div class="num font-semibold">{rupiahBrief(pt?.debt ?? 0)}</div>
			</div>
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">Arus kas/bln</div>
				<div class="num font-semibold">{rupiahBrief(pt?.cashflow ?? 0)}</div>
			</div>
		</div>

		<!-- Skor & breakdown (PRD §8) -->
		<div class="mt-4">
			<h4 class="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
				Skor rekomendasi: {(detailTwin.score * 100).toFixed(0)}/100
			</h4>
			{#if detailTwin.score_breakdown?.components}
				<div class="space-y-1.5">
					{#each Object.entries(detailTwin.score_breakdown.components as Record<string, number>) as [k, v]}
						<div class="flex items-center gap-2 text-xs">
							<span class="w-36 shrink-0 text-[var(--color-ink-dim)]">{scoreLabel[k] ?? k}</span>
							<div class="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--color-line)]">
								<div
									class="h-full rounded-full"
									style="width:{Math.min(
										100,
										(v / weightOf(k)) * 100
									)}%; background:var(--color-accent)"
								></div>
							</div>
							<span class="num w-20 text-right">{v.toFixed(3)} / {weightOf(k)}</span>
						</div>
					{/each}
				</div>
			{/if}
			{#if detailTwin.score_breakdown?.preset_scores}
				<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
					Skor per preset:
					{#each Object.entries(detailTwin.score_breakdown.preset_scores as Record<string, number>) as [k, v]}
						<span class="chip mr-1 !text-[0.65rem]">{k.slice(0, 5)}: {(v * 100).toFixed(0)}</span>
					{/each}
				</p>
			{/if}
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
						<div class="flex items-center gap-2">
							<span class="num text-xs text-[var(--color-ink-dim)]"
								>kas min {rupiahBrief(s.min_cash)}</span
							>
							<Badge level={s.survived ? 'ok' : 'red'}
								>{s.survived ? 'Bertahan' : 'Tidak bertahan'}</Badge
							>
						</div>
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

{#if result}
	<ReportModal bind:open={reportOpen} simulation={result} recommendation={sim.recommendation} />
	<PitchModal bind:open={pitchOpen} simulation={result} recommendation={sim.recommendation} />
	<ShareModal
		bind:open={shareOpen}
		twins={result.twins}
		{bestCode}
		simId={result.id}
		preset={preset ?? result.preset}
	/>
{/if}
