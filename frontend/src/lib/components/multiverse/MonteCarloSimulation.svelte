<script lang="ts">
	import type { Twin, MonteCarloResult } from '$lib/api/types';
	import { api } from '$lib/api/client';
	import { rupiahBrief, percent } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let {
		twins = [],
		simId,
		preset = 'moderat'
	}: {
		twins: Twin[];
		simId: string;
		preset?: string;
	} = $props();

	let selectedTwinCode = $state<string>('0');
	let isReal = $state<boolean>(false);
	let runsCount = $state<number>(500);

	let loading = $state<boolean>(false);
	let errorMsg = $state<string | null>(null);
	let mcData = $state<MonteCarloResult | null>(null);

	let currentTwin = $derived(twins.find((t) => t.code === selectedTwinCode) ?? twins[0]);

	/**
	 * Muat data Monte Carlo. Bergantung pada `simId`, `selectedTwinCode`,
	 * `runsCount`, dan `preset` — SATU-satunya jalur pemuatan (selector tidak
	 * lagi memanggil fungsi ini langsung) agar tidak ada request ganda.
	 */
	$effect(() => {
		// Baca semua dependency agar reaktif.
		const id = simId;
		const code = selectedTwinCode;
		const runs = runsCount;
		const p = preset;
		if (!id || !code) return;
		let cancelled = false;
		loading = true;
		errorMsg = null;
		api
			.getMonteCarlo(id, code, runs, p)
			.then((data) => {
				if (!cancelled) mcData = data;
			})
			.catch((e) => {
				if (!cancelled) errorMsg = String(e);
			})
			.finally(() => {
				if (!cancelled) loading = false;
			});
		return () => {
			cancelled = true;
		};
	});

	// SVG Dimensions
	const W = 680;
	const H = 260;
	const PAD = { l: 70, r: 24, t: 24, b: 32 };

	let pts = $derived(mcData?.yearly_percentiles ?? []);

	let maxVal = $derived.by(() => {
		if (!pts.length) return 1_000_000_000;
		const field = isReal ? 'real' : 'nominal';
		let maxN = Math.max(...pts.map((p) => Math.max(p[field].p90, 0)));
		return Math.max(maxN, 100_000_000);
	});

	let minVal = $derived.by(() => {
		if (!pts.length) return 0;
		const field = isReal ? 'real' : 'nominal';
		let minN = Math.min(...pts.map((p) => Math.min(p[field].p10, 0)));
		return Math.min(minN, 0);
	});

	function xCoord(year: number): number {
		return PAD.l + ((W - PAD.l - PAD.r) * year) / 20;
	}

	function yCoord(val: number): number {
		const range = maxVal - minVal || 1;
		const plotH = H - PAD.t - PAD.b;
		const normalized = (val - minVal) / range;
		return PAD.t + plotH * (1 - normalized);
	}

	// Band Paths
	let p10_p90_Area = $derived.by(() => {
		if (!pts.length) return '';
		const field = isReal ? 'real' : 'nominal';
		const top = pts.map((p) => `${xCoord(p.year).toFixed(1)},${yCoord(p[field].p90).toFixed(1)}`);
		const bottom = [...pts]
			.reverse()
			.map((p) => `${xCoord(p.year).toFixed(1)},${yCoord(p[field].p10).toFixed(1)}`);
		return `M ${top.join(' L ')} L ${bottom.join(' L ')} Z`;
	});

	let p25_p75_Area = $derived.by(() => {
		if (!pts.length) return '';
		const field = isReal ? 'real' : 'nominal';
		const top = pts.map((p) => `${xCoord(p.year).toFixed(1)},${yCoord(p[field].p75).toFixed(1)}`);
		const bottom = [...pts]
			.reverse()
			.map((p) => `${xCoord(p.year).toFixed(1)},${yCoord(p[field].p25).toFixed(1)}`);
		return `M ${top.join(' L ')} L ${bottom.join(' L ')} Z`;
	});

	let p50_Line = $derived.by(() => {
		if (!pts.length) return '';
		const field = isReal ? 'real' : 'nominal';
		return pts
			.map(
				(p, i) =>
					`${i === 0 ? 'M' : 'L'} ${xCoord(p.year).toFixed(1)} ${yCoord(p[field].p50).toFixed(1)}`
			)
			.join(' ');
	});

	let zeroY = $derived(yCoord(0));

	let hoverYear = $state<number>(10);
	let hoverData = $derived(pts.find((p) => p.year === hoverYear) ?? pts[10]);
</script>

<div class="card p-5">
	<!-- Header -->
	<div
		class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4"
	>
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🎲</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Simulasi Monte Carlo: Evaluasi Ketidakpastian Multiverse (P1 PRD §6)
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Uji 500 trajektori stokastik acak dengan volatilitas riil pasar modal & inflasi Indonesia
				untuk memetakan rentang hasil terburuk (P10) hingga terbaik (P90).
			</p>
		</div>

		<!-- Real vs Nominal Toggle -->
		<div class="flex items-center gap-2">
			<div
				class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs"
			>
				<button
					class="rounded-md px-2.5 py-1 font-semibold transition {!isReal
						? 'bg-[var(--color-accent)] text-white'
						: 'text-[var(--color-ink-dim)]'}"
					onclick={() => (isReal = false)}
				>
					Nominal
				</button>
				<button
					class="rounded-md px-2.5 py-1 font-semibold transition {isReal
						? 'bg-[var(--color-accent)] text-white'
						: 'text-[var(--color-ink-dim)]'}"
					onclick={() => (isReal = true)}
				>
					Nilai Riil (Net Inflasi)
				</button>
			</div>
		</div>
	</div>

	<!-- Selector Twin & Jumlah Run -->
	<div class="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs">
		<div class="flex flex-wrap items-center gap-2">
			<span class="font-semibold text-[var(--color-ink-dim)]">Pilih Skenario Twin:</span>
			<div class="flex flex-wrap gap-1.5">
				{#each twins as t}
					<button
						class="chip text-xs transition"
						class:active={selectedTwinCode === t.code}
						style="border-color: {selectedTwinCode === t.code
							? t.color
							: 'var(--color-line)'}; color: {selectedTwinCode === t.code
							? t.color
							: 'var(--color-ink)'}"
						onclick={() => (selectedTwinCode = t.code)}
					>
						<span>{twinIcon(t.icon)}</span>
						<span>Twin {t.code}: {t.label.split(' ')[1] ?? t.label}</span>
					</button>
				{/each}
			</div>
		</div>

		<div class="flex items-center gap-2">
			<span class="text-[var(--color-ink-dim)]">Jumlah Run:</span>
			<select
				class="rounded border border-[var(--color-line)] bg-[var(--color-void-1)] px-2 py-1 text-xs font-mono font-bold"
				bind:value={runsCount}
			>
				<option value={100}>100 Run (Cepat)</option>
				<option value={500}>500 Run (Standar)</option>
				<option value={1000}>1.000 Run (Presisi)</option>
			</select>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center p-12 text-xs text-[var(--color-ink-dim)]">
			<span class="animate-spin mr-2">⚙️</span> Menjalankan {runsCount} iterasi stokastik Monte Carlo…
		</div>
	{:else if errorMsg}
		<div
			class="mt-4 rounded-xl border border-[var(--color-danger)] bg-rose-500/10 p-3 text-xs text-rose-400"
		>
			{errorMsg}
		</div>
	{:else if mcData}
		<!-- Ringkasan Metrik Risiko & Keandalan di Tahun ke-10 -->
		<div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
			<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3">
				<span class="text-[11px] font-semibold text-[var(--color-ink-dim)]"
					>Probabilitas Bertahan (Th-{mcData.metrics.eval_year})</span
				>
				<div class="mt-1 text-lg font-black text-emerald-400">
					{percent(mcData.metrics.success_rate_positive_y10, 0)}
				</div>
				<p class="mt-0.5 text-[10px] text-[var(--color-ink-dim)]">Peluang kekayaan riil &gt; 0</p>
			</div>

			<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3">
				<span class="text-[11px] font-semibold text-[var(--color-ink-dim)]"
					>Pelestarian Modal (Th-{mcData.metrics.eval_year})</span
				>
				<div class="mt-1 text-lg font-black text-cyan-400">
					{percent(mcData.metrics.success_rate_wealth_preservation_y10, 0)}
				</div>
				<p class="mt-0.5 text-[10px] text-[var(--color-ink-dim)]">Mengalahkan inflasi kumulatif</p>
			</div>

			<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3">
				<span class="text-[11px] font-semibold text-[var(--color-ink-dim)]"
					>Nilai Tengah Median (P50)</span
				>
				<div class="mt-1 text-lg font-black text-[var(--color-accent)]">
					{rupiahBrief(
						isReal
							? mcData.metrics.median_net_worth_real_y10
							: mcData.metrics.median_net_worth_nominal_y10
					)}
				</div>
				<p class="mt-0.5 text-[10px] text-[var(--color-ink-dim)]">Hasil paling probabel</p>
			</div>

			<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3">
				<span class="text-[11px] font-semibold text-[var(--color-ink-dim)]"
					>Batas Bawah Skenario (P10)</span
				>
				<div class="mt-1 text-lg font-black text-rose-400">
					{rupiahBrief(mcData.metrics.p10_net_worth_y10)}
				</div>
				<p class="mt-0.5 text-[10px] text-[var(--color-ink-dim)]">Pasar bergejolak (Bear Market)</p>
			</div>
		</div>

		<!-- Grafik Fan Chart SVG -->
		<div
			class="mt-4 overflow-x-auto rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3"
		>
			<div
				class="mb-2 flex flex-wrap items-center justify-between text-xs text-[var(--color-ink-dim)]"
			>
				<div class="flex items-center gap-3">
					<span class="flex items-center gap-1.5">
						<span
							class="inline-block h-2.5 w-5 rounded-sm opacity-25"
							style="background: {currentTwin?.color ?? 'var(--color-accent)'};"
						></span>
						<span>Rentang 90% (P10–P90)</span>
					</span>
					<span class="flex items-center gap-1.5">
						<span
							class="inline-block h-2.5 w-5 rounded-sm opacity-55"
							style="background: {currentTwin?.color ?? 'var(--color-accent)'};"
						></span>
						<span>Rentang 50% (P25–P75)</span>
					</span>
					<span class="flex items-center gap-1.5">
						<span
							class="inline-block h-1 w-5"
							style="background: {currentTwin?.color ?? 'var(--color-accent)'};"
						></span>
						<strong class="text-[var(--color-ink)]">Median P50</strong>
					</span>
				</div>
				<span class="text-[11px]">Hover slider di bawah untuk rincian tahun</span>
			</div>

			<svg viewBox="0 0 {W} {H}" class="w-full min-w-[540px]">
				<!-- Garis Nol Net Worth -->
				{#if zeroY >= PAD.t && zeroY <= H - PAD.b}
					<line
						x1={PAD.l}
						y1={zeroY}
						x2={W - PAD.r}
						y2={zeroY}
						stroke="var(--color-line)"
						stroke-dasharray="3 3"
						stroke-width="1"
					/>
					<text
						x={PAD.l - 6}
						y={zeroY + 3}
						text-anchor="end"
						font-size="9"
						fill="var(--color-ink-dim)"
					>
						Rp 0
					</text>
				{/if}

				<!-- Sumbu Y Marks -->
				<text
					x={PAD.l - 6}
					y={yCoord(maxVal) + 8}
					text-anchor="end"
					font-size="9"
					fill="var(--color-ink-dim)"
				>
					{rupiahBrief(maxVal)}
				</text>

				<!-- Area Pita P10-P90 (Shaded Outer Cone) -->
				<path d={p10_p90_Area} fill={currentTwin?.color ?? 'var(--color-accent)'} opacity="0.22" />

				<!-- Area Pita P25-P75 (Shaded Inner Core) -->
				<path d={p25_p75_Area} fill={currentTwin?.color ?? 'var(--color-accent)'} opacity="0.38" />

				<!-- Garis Tengah P50 -->
				<path
					d={p50_Line}
					fill="none"
					stroke={currentTwin?.color ?? 'var(--color-accent)'}
					stroke-width="2.5"
				/>

				<!-- Indikator Vertikal Hover Year -->
				{#if hoverYear >= 0 && hoverYear <= 20}
					{@const hX = xCoord(hoverYear)}
					<line
						x1={hX}
						y1={PAD.t}
						x2={hX}
						y2={H - PAD.b}
						stroke="var(--color-ink-dim)"
						stroke-width="1"
						stroke-dasharray="2 2"
					/>
					<circle
						cx={hX}
						cy={yCoord(hoverData ? (isReal ? hoverData.real.p50 : hoverData.nominal.p50) : 0)}
						r="4"
						fill={currentTwin?.color ?? 'var(--color-accent)'}
					/>
				{/if}

				<!-- Sumbu X Label Tahun (0, 5, 10, 15, 20) -->
				{#each [0, 5, 10, 15, 20] as yr}
					<text
						x={xCoord(yr)}
						y={H - PAD.b + 18}
						text-anchor="middle"
						font-size="10"
						fill="var(--color-ink-dim)"
					>
						Th-{yr}
					</text>
				{/each}
			</svg>

			<!-- Scrubber Interaktif Tahun -->
			<div class="mt-3 flex items-center gap-3 border-t border-[var(--color-line)] pt-2.5">
				<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Tinjau Tahun:</span>
				<input
					type="range"
					min="0"
					max="20"
					step="1"
					class="w-48 accent-[var(--color-accent)]"
					bind:value={hoverYear}
				/>
				<span class="text-xs font-bold text-[var(--color-ink)]">Tahun ke-{hoverYear}</span>

				{#if hoverData}
					{@const hVals = isReal ? hoverData.real : hoverData.nominal}
					<div class="ml-auto flex flex-wrap gap-2 text-[11px]">
						<span class="text-rose-400">P10: <strong>{rupiahBrief(hVals.p10)}</strong></span>
						<span class="text-[var(--color-ink-dim)]"
							>P25: <strong>{rupiahBrief(hVals.p25)}</strong></span
						>
						<span class="text-cyan-400">P50: <strong>{rupiahBrief(hVals.p50)}</strong></span>
						<span class="text-[var(--color-ink-dim)]"
							>P75: <strong>{rupiahBrief(hVals.p75)}</strong></span
						>
						<span class="text-emerald-400">P90: <strong>{rupiahBrief(hVals.p90)}</strong></span>
					</div>
				{/if}
			</div>
		</div>

		<!-- Footer Insight Pasar Keuangan RI -->
		<div class="mt-3 text-[11px] leading-relaxed text-[var(--color-ink-dim)]">
			💡 <strong>Pita Probabilitas Monte Carlo:</strong> Berbeda dengan garis lurus proyeksi deterministik,
			pasar riil bergerak secara acak. Lebar pita mencerminkan derajat ketidakpastian instrumen: portofolio
			saham (Twin V) memiliki pita P10-P90 yang sangat lebar karena volatilitas IHSG (σ ~16%), sedangkan
			SBN dan pasar uang (Twin B / Twin R) memiliki pita yang jauh lebih padat dan terprediksi.
		</div>
	{/if}
</div>
