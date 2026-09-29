<script lang="ts">
	import type { Simulation, Recommendation, Twin } from '$lib/api/types';
	import { rupiahBrief } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let {
		open = $bindable(false),
		simulation,
		recommendation
	}: {
		open: boolean;
		simulation: Simulation;
		recommendation: Recommendation | null;
	} = $props();

	let currentSlide = $state(0);

	// Kunci scroll body saat presentasi terbuka, dan mulai selalu dari slide
	// pertama. Sebelumnya `currentSlide` bertahan setelah modal ditutup sehingga
	// membuka lagi melanjutkan dari slide terakhir, dan halaman di belakang
	// overlay masih bisa ter-scroll.
	$effect(() => {
		if (typeof document === 'undefined') return;
		if (open) {
			currentSlide = 0;
			document.body.style.overflow = 'hidden';
		}
		return () => {
			document.body.style.overflow = '';
		};
	});

	let bestTwin = $derived(
		simulation.twins.find((t) => t.code === (recommendation?.best_twin ?? simulation.best_twin))
	);

	let gapYear10 = $derived.by(() => {
		if (simulation.twins.length < 2) return null;
		const sorted = [...simulation.twins].sort(
			(a, b) =>
				(b.yearly_series.find((p) => p.year === 10)?.net_worth_real ?? 0) -
				(a.yearly_series.find((p) => p.year === 10)?.net_worth_real ?? 0)
		);
		const top = sorted[0];
		const bottom = sorted[sorted.length - 1];
		const topVal = top.yearly_series.find((p) => p.year === 10)?.net_worth_real ?? 0;
		const botVal = bottom.yearly_series.find((p) => p.year === 10)?.net_worth_real ?? 0;
		return {
			top,
			bottom,
			diff: topVal - botVal,
			topVal,
			botVal
		};
	});

	let fastest100m = $derived.by(() => {
		const reached = simulation.twins
			.map((t) => ({ twin: t, month: t.milestones?.net_worth_100m }))
			.filter((x): x is { twin: Twin; month: number } => typeof x.month === 'number');
		if (!reached.length) return null;
		reached.sort((a, b) => a.month - b.month);
		return reached[0];
	});

	function next() {
		if (currentSlide < 3) currentSlide++;
	}

	function prev() {
		if (currentSlide > 0) currentSlide--;
	}

	function onkeydown(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'ArrowRight' || e.key === ' ') {
			e.preventDefault();
			next();
		} else if (e.key === 'ArrowLeft') {
			e.preventDefault();
			prev();
		} else if (e.key === 'Escape') {
			open = false;
		}
	}
</script>

<svelte:window {onkeydown} />

{#if open}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4 sm:p-8 backdrop-blur-md"
		role="dialog"
		aria-modal="true"
	>
		<div
			class="relative flex h-[90vh] max-h-[700px] w-full max-w-4xl flex-col justify-between rounded-3xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-6 sm:p-10 shadow-2xl"
		>
			<!-- Top Bar -->
			<div class="flex items-center justify-between border-b border-[var(--color-line)] pb-4">
				<div class="flex items-center gap-2">
					<span
						class="rounded-lg bg-blue-500/20 px-2 py-1 text-xs font-bold text-[var(--color-accent)]"
					>
						MODE PRESENTASI JURI
					</span>
					<span class="text-xs text-[var(--color-ink-dim)]">Financial Twin · 60s Aha Moment</span>
				</div>

				<div class="flex items-center gap-2">
					<!-- Slide indicators -->
					<div class="flex gap-1.5 mr-4">
						{#each [0, 1, 2, 3] as s}
							<button
								class="h-2 w-8 rounded-full transition-colors"
								class:bg-[var(--color-accent)]={currentSlide === s}
								class:bg-[var(--color-void-3)]={currentSlide !== s}
								onclick={() => (currentSlide = s)}
								aria-label={`Slide ${s + 1}`}
							></button>
						{/each}
					</div>
					<button
						class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-void-3)] text-sm font-bold hover:bg-[var(--color-line)]"
						onclick={() => (open = false)}
					>
						✕
					</button>
				</div>
			</div>

			<!-- Slide Content Area -->
			<div class="my-auto flex flex-col items-center justify-center text-center">
				{#if currentSlide === 0}
					<!-- Slide 1: Multiverse Bercabang -->
					<div class="max-w-2xl space-y-4">
						<div class="text-5xl">🌌</div>
						<h2 class="text-2xl font-black tracking-tight sm:text-3xl text-[var(--color-ink)]">
							Satu Keputusan, Tiga Masa Depan Paralel
						</h2>
						<p class="text-sm leading-relaxed text-[var(--color-ink-dim)]">
							Daripada sekadar mengira-ngira, Financial Twin memproyeksikan dirimu di 3–4 jalur
							multiverse secara deterministik selama 240 bulan (20 tahun).
						</p>

						<div class="mt-6 flex flex-wrap justify-center gap-3">
							{#each simulation.twins as t}
								<div
									class="flex items-center gap-2 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] px-4 py-2.5 shadow-sm"
								>
									<span class="font-bold text-base" style="color:{t.color}">{twinIcon(t.icon)}</span
									>
									<div class="text-left">
										<div class="text-xs font-bold">Twin {t.code}: {t.label}</div>
										<div class="text-[10px] text-[var(--color-ink-dim)]">
											{t.code === '0' ? 'Baseline status quo' : 'Keputusan paralel'}
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{:else if currentSlide === 1}
					<!-- Slide 2: The Wealth Gap & Opportunity Cost -->
					<div class="max-w-2xl space-y-4">
						<div class="text-5xl">⚖️</div>
						<h2 class="text-2xl font-black tracking-tight sm:text-3xl text-[var(--color-ink)]">
							Opportunity Cost Nyata di Tahun ke-10
						</h2>
						<p class="text-sm leading-relaxed text-[var(--color-ink-dim)]">
							Perbedaan kecil pada keputusan konsumtif vs produktif hari ini menciptakan jurang
							kekayaan riil yang sangat masif di masa depan:
						</p>

						{#if gapYear10}
							<div
								class="mt-4 rounded-2xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-6"
							>
								<div
									class="text-xs uppercase tracking-wider text-[var(--color-ink-dim)] font-semibold"
								>
									Selisih Kekayaan Riil (Tahun ke-10)
								</div>
								<div class="num mt-2 text-4xl font-extrabold text-[var(--color-accent)]">
									{rupiahBrief(gapYear10.diff)}
								</div>
								<div class="mt-3 flex justify-around text-xs text-[var(--color-ink-dim)]">
									<div>
										<span class="font-bold text-emerald-400"
											>Twin {gapYear10.top.code} ({gapYear10.top.label}):</span
										>
										<div class="num font-bold text-sm text-[var(--color-ink)]">
											{rupiahBrief(gapYear10.topVal)}
										</div>
									</div>
									<div class="border-l border-[var(--color-line)]"></div>
									<div>
										<span class="font-bold text-rose-400"
											>Twin {gapYear10.bottom.code} ({gapYear10.bottom.label}):</span
										>
										<div class="num font-bold text-sm text-[var(--color-ink)]">
											{rupiahBrief(gapYear10.botVal)}
										</div>
									</div>
								</div>
								{#if fastest100m}
									<div
										class="mt-3 border-t border-[var(--color-line)] pt-3 text-xs text-emerald-400 font-semibold text-center"
									>
										🚀 100 Juta Pertama: Twin {fastest100m.twin.code} ({fastest100m.twin.label})
										mencapai di {fastest100m.month === 0
											? 'Bulan ke-0 (Awal)'
											: `Bulan ke-${fastest100m.month}`}
									</div>
								{/if}
							</div>
						{/if}
					</div>
				{:else if currentSlide === 2}
					<!-- Slide 3: Stress Testing -->
					<div class="max-w-2xl space-y-4">
						<div class="text-5xl">⚡</div>
						<h2 class="text-2xl font-black tracking-tight sm:text-3xl text-[var(--color-ink)]">
							Siapa yang Bertahan Saat Krisis Melanda?
						</h2>
						<p class="text-sm leading-relaxed text-[var(--color-ink-dim)]">
							Uji guncangan instan: kehilangan penghasilan 3 bulan dan biaya darurat 2×. Jalur mana
							yang runtuh dan harus berutang baru?
						</p>

						<div class="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2 text-left">
							{#each simulation.twins as t}
								{@const jobShock =
									t.stress.find((s) => s.shock === 'income_loss_3m') ?? t.stress[0]}
								<div
									class="rounded-xl border p-3.5 transition-all {jobShock?.survived
										? 'border-emerald-500 bg-emerald-500/5'
										: 'border-rose-500 bg-rose-500/5'}"
								>
									<div class="flex items-center justify-between">
										<div class="flex items-center gap-1.5 font-bold text-xs">
											<span style="color:{t.color}">{twinIcon(t.icon)}</span>
											<span>Twin {t.code}: {t.label}</span>
										</div>
										<span
											class="text-xs font-bold {jobShock?.survived
												? 'text-emerald-400'
												: 'text-rose-400'}"
										>
											{jobShock?.survived ? '✓ Lolos' : '✗ Runtuh'}
										</span>
									</div>
									<div class="mt-1 text-[11px] text-[var(--color-ink-dim)]">
										{jobShock?.survived
											? 'Bantalan kas likuid mencukupi.'
											: 'Kas habis, terpaksa berutang darurat.'}
									</div>
								</div>
							{/each}
						</div>
					</div>
				{:else}
					<!-- Slide 4: Rekomendasi & First Step -->
					<div class="max-w-2xl space-y-4">
						<div class="text-5xl">🎯</div>
						<h2 class="text-2xl font-black tracking-tight sm:text-3xl text-[var(--color-ink)]">
							Rekomendasi Berbasis Bukti & Langkah Aksi
						</h2>
						<p class="text-sm leading-relaxed text-[var(--color-ink-dim)]">
							Bukan sekadar kalkulator statis. Sistem memberikan satu langkah pertama konkret hari
							ini:
						</p>

						{#if recommendation && bestTwin}
							<div
								class="mt-4 rounded-2xl border border-[var(--color-accent)] bg-blue-500/10 p-6 text-left"
							>
								<div class="flex items-center gap-2">
									<span
										class="rounded-full px-2.5 py-1 text-xs font-bold text-black"
										style="background:{bestTwin.color}"
									>
										Pilihan Terbaik: Twin {bestTwin.code} — {bestTwin.label}
									</span>
									<span class="text-xs text-[var(--color-ink-dim)] font-mono">
										(Skor {(bestTwin.score * 100).toFixed(0)}/100)
									</span>
								</div>

								<div class="mt-3 text-sm font-bold text-[var(--color-ink)]">
									👉 {recommendation.first_step}
								</div>

								<p class="mt-2 text-xs leading-relaxed text-[var(--color-ink-dim)]">
									{recommendation.rationale}
								</p>
							</div>
						{/if}
					</div>
				{/if}
			</div>

			<!-- Bottom Navigation -->
			<div class="flex items-center justify-between border-t border-[var(--color-line)] pt-4">
				<button class="btn btn-ghost !py-2 text-xs" onclick={prev} disabled={currentSlide === 0}>
					← Sebelumnya
				</button>

				<div class="text-xs text-[var(--color-ink-dim)]">
					Gunakan tombol panah keyboard ← → untuk navigasi
				</div>

				{#if currentSlide < 3}
					<button class="btn btn-primary !py-2 text-xs" onclick={next}> Lanjut → </button>
				{:else}
					<button class="btn btn-primary !py-2 text-xs" onclick={() => (open = false)}>
						Selesai ✓
					</button>
				{/if}
			</div>
		</div>
	</div>
{/if}
