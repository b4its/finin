<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { replaceState } from '$app/navigation';
	import { history } from '$lib/stores/history.svelte';
	import { toast } from '$lib/stores/toast.svelte';
	import { api } from '$lib/api/client';
	import { dateID, rupiahBrief, percent, months } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';
	import type { Simulation, Twin } from '$lib/api/types';

	const MAX_SELECT = 3;

	onMount(() => history.load());

	/** ID simulasi yang dicentang untuk dibandingkan (maks MAX_SELECT). */
	let selected = $state<string[]>(
		[...new Set(page.url.searchParams.get('ids')?.split(',').filter(Boolean) ?? [])].slice(
			0,
			MAX_SELECT
		)
	);
	let loaded = $state<Record<string, Simulation>>({});
	let loadingIds = $state<Record<string, boolean>>({});
	let errorIds = $state<Record<string, string>>({});

	function toggle(id: string) {
		if (selected.includes(id)) {
			selected = selected.filter((x) => x !== id);
			syncUrl();
			return;
		}
		if (selected.length >= MAX_SELECT) {
			toast.warn(`Maksimal ${MAX_SELECT} simulasi untuk dibandingkan sekaligus.`);
			return;
		}
		selected = [...selected, id];
		syncUrl();
		void ensureLoaded(id);
	}

	function clearSelection() {
		selected = [];
		syncUrl();
	}

	/** Simpan pilihan di URL agar perbandingan bisa dibagikan dan dipulihkan. */
	function syncUrl() {
		const url = new URL(page.url);
		if (selected.length) url.searchParams.set('ids', selected.join(','));
		else url.searchParams.delete('ids');
		replaceState(`${url.pathname}${url.search}${url.hash}`, {});
	}

	async function ensureLoaded(id: string) {
		if (loaded[id] || loadingIds[id]) return;
		loadingIds = { ...loadingIds, [id]: true };
		try {
			const res = await api.getSimulation(id);
			loaded = { ...loaded, [id]: res };
		} catch (e) {
			errorIds = { ...errorIds, [id]: String(e) };
		} finally {
			loadingIds = { ...loadingIds, [id]: false };
		}
	}

	// Muat data untuk semua item yang terpilih (mis. saat datang dari tautan ?ids=).
	$effect(() => {
		for (const id of selected) void ensureLoaded(id);
	});

	let selectedSims = $derived(
		selected
			.map((id) => ({ id, sim: loaded[id], error: errorIds[id], loading: loadingIds[id] }))
			.filter((x) => x.sim || x.error || x.loading)
	);

	let comparable = $derived(selectedSims.filter((x) => x.sim).map((x) => x.sim as Simulation));

	/** Twin terbaik dari tiap simulasi, plus ringkasan tahun ke-10. */
	function bestTwin(sim: Simulation): Twin | undefined {
		return sim.twins.find((t) => t.code === sim.best_twin);
	}

	interface Row {
		id: string;
		label: string;
		preset: string;
		branches: number;
		bestCode: string;
		bestLabel: string;
		color: string;
		netWorthY10: number;
		netWorthRealY10: number;
		emergencyMonths: number;
		avgDsr: number;
		score: number;
		robust: boolean;
	}

	let rows = $derived.by<Row[]>(() =>
		comparable.map((sim) => {
			const bt = bestTwin(sim);
			const y10 = bt?.yearly_series.find((p) => p.year === 10);
			const summary = (bt?.summary ?? {}) as Record<string, unknown>;
			const rec = history.items.find((r) => r.id === sim.id);
			return {
				id: sim.id,
				label: rec?.label || `Simulasi ${sim.id.slice(0, 8)}`,
				preset: sim.preset,
				branches: sim.twins.length,
				bestCode: sim.best_twin,
				bestLabel: bt?.label ?? sim.best_twin,
				color: bt?.color ?? '#60a5fa',
				netWorthY10: y10?.net_worth ?? 0,
				netWorthRealY10: y10?.net_worth_real ?? 0,
				emergencyMonths: y10?.emergency_months ?? 0,
				avgDsr: Number(summary.avg_dsr ?? y10?.dsr ?? 0),
				score: (bt?.score ?? 0) * 100,
				robust: sim.robust
			};
		})
	);

	/** Nilai terbaik untuk menyorot kolom unggulan. */
	let maxNetWorth = $derived(Math.max(1, ...rows.map((r) => r.netWorthRealY10)));
	let maxScore = $derived(Math.max(1, ...rows.map((r) => r.score)));
	let minDsr = $derived(Math.min(...rows.map((r) => r.avgDsr)));

	function exportComparisonCsv() {
		if (!rows.length) return;
		const header = [
			'label',
			'preset',
			'cabang',
			'twin_terbaik',
			'net_worth_th10',
			'net_worth_riil_th10',
			'dana_darurat_bulan',
			'avg_dsr',
			'skor',
			'robust'
		];
		const lines = rows.map((r) =>
			[
				`"${r.label.replace(/"/g, '""')}"`,
				r.preset,
				r.branches,
				r.bestCode,
				Math.round(r.netWorthY10),
				Math.round(r.netWorthRealY10),
				r.emergencyMonths.toFixed(1),
				(r.avgDsr * 100).toFixed(1) + '%',
				r.score.toFixed(0),
				r.robust ? 'ya' : 'tidak'
			].join(',')
		);
		const csv = [header.join(','), ...lines].join('\n');
		downloadBlob(csv, 'text/csv;charset=utf-8', 'csv');
		toast.success('CSV perbandingan diunduh');
	}

	/** Ekspor paket perbandingan lengkap sebagai JSON terstruktur. */
	function exportComparisonJson() {
		if (!rows.length) return;
		const payload = {
			exported_at: new Date().toISOString(),
			metric_notes:
				'net_worth_* dalam Rupiah; avg_dsr & skor_fraksi adalah rasio 0..1; skor_100 = skor_fraksi × 100.',
			simulations: rows.map((r) => ({
				id: r.id,
				label: r.label,
				preset: r.preset,
				branches: r.branches,
				best_twin: r.bestCode,
				best_label: r.bestLabel,
				net_worth_y10: Math.round(r.netWorthY10),
				net_worth_real_y10: Math.round(r.netWorthRealY10),
				emergency_months: r.emergencyMonths,
				avg_dsr: r.avgDsr,
				skor_fraksi: r.score / 100,
				skor_100: Number(r.score.toFixed(1)),
				robust: r.robust
			}))
		};
		downloadBlob(JSON.stringify(payload, null, 2), 'application/json;charset=utf-8', 'json');
		toast.success('JSON perbandingan diunduh');
	}

	function downloadBlob(content: string, type: string, ext: string) {
		const blob = new Blob([content], { type });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `perbandingan-simulasi-${Date.now()}.${ext}`;
		a.click();
		URL.revokeObjectURL(url);
	}

	/** Bagikan tautan perbandingan (berisi daftar id) ke clipboard. */
	async function copyShareLink() {
		const url = new URL(page.url);
		if (selected.length) url.searchParams.set('ids', selected.join(','));
		else url.searchParams.delete('ids');
		try {
			await navigator.clipboard.writeText(url.toString());
			toast.success('Tautan perbandingan disalin');
		} catch {
			toast.error('Gagal menyalin tautan — salin manual dari address bar');
		}
	}
</script>

<svelte:head><title>Bandingkan simulasi — Financial Twin</title></svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8 sm:px-5">
	<div class="flex flex-wrap items-start justify-between gap-3">
		<div>
			<h1 class="text-2xl font-bold">⚖️ Bandingkan simulasi</h1>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Pilih hingga {MAX_SELECT} simulasi dari riwayatmu untuk dibandingkan berdampingan.
			</p>
		</div>
		{#if rows.length >= 2}
			<div class="flex flex-wrap items-center gap-2">
				<button class="btn btn-ghost !py-1.5 !text-xs" onclick={copyShareLink}>
					🔗 Salin tautan
				</button>
				<button class="btn btn-ghost !py-1.5 !text-xs" onclick={exportComparisonCsv}>
					📥 Unduh CSV
				</button>
				<button class="btn btn-ghost !py-1.5 !text-xs" onclick={exportComparisonJson}>
					💾 Unduh JSON
				</button>
			</div>
		{/if}
	</div>

	{#if !history.items.length && !selected.length}
		<div class="card mt-6 p-8 text-center">
			<p class="text-3xl" aria-hidden="true">🌌</p>
			<p class="mt-3 font-semibold">Belum ada simulasi untuk dibandingkan</p>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Buat minimal 2 simulasi, lalu kembali ke halaman ini.
			</p>
			<a href="/start" class="btn btn-primary mt-5 !px-6 !py-2.5">Mulai simulasi →</a>
		</div>
	{:else}
		<!-- Pemilih simulasi lokal; hasil deep-link tetap tampil tanpa riwayat penerima. -->
		{#if history.items.length}
			<section class="mt-5" aria-label="Pilih simulasi">
				<div class="mb-2 flex items-center justify-between">
					<h2 class="text-sm font-semibold">Pilih simulasi ({selected.length}/{MAX_SELECT})</h2>
					{#if selected.length}
						<button
							class="text-xs text-[var(--color-ink-dim)] hover:underline"
							onclick={clearSelection}>Bersihkan pilihan</button
						>
					{/if}
				</div>
				<div class="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
					{#each history.items as r (r.id)}
						{@const on = selected.includes(r.id)}
						<button
							type="button"
							class="card card-interactive flex items-start gap-3 p-3 text-left {on
								? '!border-[var(--color-accent)] bg-[rgba(96,165,250,0.08)]'
								: ''}"
							aria-pressed={on}
							onclick={() => toggle(r.id)}
						>
							<span
								class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border text-[10px] {on
									? 'border-[var(--color-accent)] bg-[var(--color-accent)] text-slate-950'
									: 'border-[var(--color-line)]'}"
								aria-hidden="true">{on ? '✓' : ''}</span
							>
							<span class="min-w-0 flex-1">
								<span class="block truncate text-xs font-semibold"
									>{r.label || `Simulasi ${r.id.slice(0, 8)}`}</span
								>
								<span class="mt-0.5 block text-[11px] text-[var(--color-ink-dim)]">
									{r.twin_count} cabang · {r.preset} · {dateID(
										new Date(r.created_at).toISOString()
									)}
								</span>
							</span>
						</button>
					{/each}
				</div>
			</section>
		{/if}

		<!-- Hasil perbandingan -->
		{#if selectedSims.some((x) => x.loading) && !rows.length}
			<div class="card mt-6 h-64 skeleton" aria-busy="true" aria-live="polite"></div>
		{/if}

		{#if selectedSims.some((x) => x.error)}
			<div class="card mt-6 border-[var(--color-danger)] p-4 text-sm">
				<p class="font-semibold text-[var(--color-danger)]">Sebagian simulasi gagal dimuat</p>
				<ul class="mt-1 space-y-0.5 text-xs text-[var(--color-ink-dim)]">
					{#each selectedSims.filter((x) => x.error) as x (x.id)}
						<li>• {x.id.slice(0, 8)}: {x.error}</li>
					{/each}
				</ul>
				<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
					Simulasi kedaluwarsa setelah 30 hari (kebijakan retensi) dan tidak lagi tersedia di
					server.
				</p>
			</div>
		{/if}

		{#if rows.length}
			{#if rows.length < 2}
				<div class="card mt-6 p-4 text-sm text-[var(--color-ink-dim)]">
					Pilih minimal <strong class="text-[var(--color-ink)]">2 simulasi</strong> untuk melihat perbandingan
					berdampingan.
				</div>
			{/if}

			<!-- Kartu mobile menjaga semua simulasi terlihat tanpa scroll horizontal. -->
			<section class="mt-6 space-y-3 sm:hidden" aria-label="Ringkasan perbandingan">
				{#each rows as r (r.id)}
					<article class="card overflow-hidden">
						<div class="border-b border-[var(--color-line)] p-4">
							<div class="flex items-start justify-between gap-3">
								<div class="min-w-0">
									<h2 class="truncate text-sm font-bold" style="color:{r.color}">{r.label}</h2>
									<p class="mt-0.5 text-[11px] text-[var(--color-ink-dim)]">
										{r.preset} · {r.branches} cabang{r.robust ? ' · robust' : ''}
									</p>
								</div>
								<a href={`/sim/${r.id}`} class="btn btn-ghost shrink-0 !px-3 !py-1.5 !text-xs"
									>Buka</a
								>
							</div>
						</div>
						<dl class="grid grid-cols-2 gap-px bg-[var(--color-line-soft)]">
							<div class="bg-[var(--color-panel)] p-3">
								<dt class="text-[10px] text-[var(--color-ink-dim)]">Twin terbaik</dt>
								<dd class="mt-1 text-xs font-semibold">{r.bestCode} — {r.bestLabel}</dd>
							</div>
							<div class="bg-[var(--color-panel)] p-3">
								<dt class="text-[10px] text-[var(--color-ink-dim)]">Net worth riil th-10</dt>
								<dd
									class="num mt-1 text-xs font-semibold"
									class:text-[var(--color-ok)]={r.netWorthRealY10 === maxNetWorth}
								>
									{rupiahBrief(r.netWorthRealY10)}{r.netWorthRealY10 === maxNetWorth ? ' ★' : ''}
								</dd>
							</div>
							<div class="bg-[var(--color-panel)] p-3">
								<dt class="text-[10px] text-[var(--color-ink-dim)]">Dana darurat</dt>
								<dd class="num mt-1 text-xs font-semibold">{months(r.emergencyMonths)}</dd>
							</div>
							<div class="bg-[var(--color-panel)] p-3">
								<dt class="text-[10px] text-[var(--color-ink-dim)]">Rata-rata DSR</dt>
								<dd
									class="num mt-1 text-xs font-semibold"
									class:text-[var(--color-ok)]={r.avgDsr === minDsr && r.avgDsr > 0}
								>
									{percent(r.avgDsr, 1)}
								</dd>
							</div>
						</dl>
						<div class="flex items-center justify-between p-3 text-xs">
							<span class="text-[var(--color-ink-dim)]">Skor rekomendasi</span>
							<strong class="num" class:text-[var(--color-ok)]={r.score === maxScore}
								>{r.score.toFixed(0)}/100</strong
							>
						</div>
					</article>
				{/each}
			</section>

			<!-- Tabel desktop memberi pemindaian metrik lintas kolom yang lebih cepat. -->
			<section class="mt-6 hidden overflow-x-auto sm:block" aria-label="Tabel perbandingan">
				<table class="w-full min-w-[36rem] border-collapse text-sm">
					<caption class="sr-only">Perbandingan metrik kunci antar simulasi terpilih</caption>
					<thead>
						<tr class="border-b border-[var(--color-line)]">
							<th scope="col" class="px-3 py-2 text-left text-xs text-[var(--color-ink-dim)]">
								Metrik
							</th>
							{#each rows as r (r.id)}
								<th scope="col" class="px-3 py-2 text-left">
									<div class="flex items-center gap-2">
										<span aria-hidden="true">{twinIcon('circle')}</span>
										<span class="truncate text-xs font-semibold" style="color:{r.color}"
											>{r.label}</span
										>
									</div>
									<div class="mt-0.5 text-[10px] font-normal text-[var(--color-ink-dim)]">
										{r.preset}{r.robust ? ' · robust' : ''}
									</div>
								</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						<tr class="border-b border-[var(--color-line-soft)]">
							<th scope="row" class="px-3 py-2 text-left text-xs text-[var(--color-ink-dim)]">
								Cabang
							</th>
							{#each rows as r (r.id)}
								<td class="num px-3 py-2">{r.branches}</td>
							{/each}
						</tr>
						<tr class="border-b border-[var(--color-line-soft)]">
							<th scope="row" class="px-3 py-2 text-left text-xs text-[var(--color-ink-dim)]">
								Twin terbaik
							</th>
							{#each rows as r (r.id)}
								<td class="px-3 py-2 text-xs">{r.bestCode} — {r.bestLabel}</td>
							{/each}
						</tr>
						<tr class="border-b border-[var(--color-line-soft)]">
							<th scope="row" class="px-3 py-2 text-left text-xs text-[var(--color-ink-dim)]">
								Net worth riil th-10
							</th>
							{#each rows as r (r.id)}
								<td
									class="num px-3 py-2 font-semibold {r.netWorthRealY10 === maxNetWorth
										? 'text-[var(--color-ok)]'
										: ''}"
								>
									{rupiahBrief(r.netWorthRealY10)}
									{#if r.netWorthRealY10 === maxNetWorth}<span class="ml-1 text-[10px]">★</span
										>{/if}
								</td>
							{/each}
						</tr>
						<tr class="border-b border-[var(--color-line-soft)]">
							<th scope="row" class="px-3 py-2 text-left text-xs text-[var(--color-ink-dim)]">
								Dana darurat
							</th>
							{#each rows as r (r.id)}
								<td class="num px-3 py-2">{months(r.emergencyMonths)}</td>
							{/each}
						</tr>
						<tr class="border-b border-[var(--color-line-soft)]">
							<th scope="row" class="px-3 py-2 text-left text-xs text-[var(--color-ink-dim)]">
								Rata-rata DSR
							</th>
							{#each rows as r (r.id)}
								<td
									class="num px-3 py-2 {r.avgDsr === minDsr && r.avgDsr > 0
										? 'text-[var(--color-ok)]'
										: ''}"
								>
									{percent(r.avgDsr, 1)}
								</td>
							{/each}
						</tr>
						<tr>
							<th scope="row" class="px-3 py-2 text-left text-xs text-[var(--color-ink-dim)]">
								Skor rekomendasi
							</th>
							{#each rows as r (r.id)}
								<td class="px-3 py-2">
									<div class="flex items-center gap-2">
										<span
											class="num text-xs font-bold {r.score === maxScore
												? 'text-[var(--color-ok)]'
												: ''}">{r.score.toFixed(0)}</span
										>
										<span class="h-1.5 w-16 overflow-hidden rounded-full bg-[var(--color-line)]">
											<span
												class="block h-full rounded-full"
												style="width:{(r.score / maxScore) * 100}%; background:{r.color}"
											></span>
										</span>
									</div>
								</td>
							{/each}
						</tr>
					</tbody>
				</table>
			</section>

			<!-- Bagan batang net worth riil th-10 -->
			{#if rows.length >= 2}
				<section class="card mt-6 p-5" aria-label="Bagan net worth tahun ke-10">
					<h2 class="text-sm font-semibold">Net worth riil tahun ke-10</h2>
					<div class="mt-4 space-y-3">
						{#each rows as r (r.id)}
							<div>
								<div class="mb-1 flex items-center justify-between text-xs">
									<span class="truncate" style="color:{r.color}">{r.label}</span>
									<span class="num font-semibold">{rupiahBrief(r.netWorthRealY10)}</span>
								</div>
								<div class="h-2.5 overflow-hidden rounded-full bg-[var(--color-void-3)]">
									<div
										class="h-full rounded-full"
										style="width:{Math.max(
											2,
											(r.netWorthRealY10 / maxNetWorth) * 100
										)}%; background:{r.color}"
									></div>
								</div>
							</div>
						{/each}
					</div>
				</section>
			{/if}

			<p class="mt-4 text-xs text-[var(--color-ink-dim)]">
				Perbandingan memakai twin terbaik tiap simulasi dan nilai riil (disesuaikan inflasi) agar
				setara antar waktu.
			</p>
		{/if}
	{/if}

	<div class="mt-8">
		<Disclaimer variant="compact" />
	</div>
</div>
