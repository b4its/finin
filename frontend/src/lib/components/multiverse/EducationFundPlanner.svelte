<script lang="ts">
	import type { Twin, Profile } from '$lib/api/types';
	import { rupiah, rupiahBrief, percent } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	interface Props {
		twins: Twin[];
		profile?: Profile;
	}

	let { twins }: Props = $props();

	interface EducationPreset {
		id: string;
		label: string;
		sub: string;
		defaultCost: number;
		defaultYears: number;
		icon: string;
	}

	const EDU_PRESETS: EducationPreset[] = [
		{
			id: 'sd_swasta',
			label: 'SD Swasta Favorit / Bilingual',
			sub: 'Uang pangkal & operasional tahun pertama',
			defaultCost: 35_000_000,
			defaultYears: 3,
			icon: '🎒'
		},
		{
			id: 'smp_swasta',
			label: 'SMP Unggulan / Boarding',
			sub: 'Pendaftaran, seragam, & uang asrama',
			defaultCost: 50_000_000,
			defaultYears: 6,
			icon: '📚'
		},
		{
			id: 'sma_unggulan',
			label: 'SMA Favorit / IB Diploma',
			sub: 'Persiapan kuliah & sertifikasi internasional',
			defaultCost: 75_000_000,
			defaultYears: 9,
			icon: '🏫'
		},
		{
			id: 's1_ptn',
			label: 'S1 PTN Top (Jalur Mandiri)',
			sub: 'UKT 8 semester + IPI / Sumbangan Gedung',
			defaultCost: 80_000_000,
			defaultYears: 12,
			icon: '🎓'
		},
		{
			id: 's1_pts',
			label: 'S1 Kampus Swasta Favorit',
			sub: 'Fakultas Kedokteran / Bisnis / Teknik',
			defaultCost: 200_000_000,
			defaultYears: 12,
			icon: '🏛️'
		},
		{
			id: 's1_overseas',
			label: 'S1 Universitas Luar Negeri',
			sub: 'Tuition fee + living cost (Aus / SG / UK)',
			defaultCost: 950_000_000,
			defaultYears: 15,
			icon: '✈️'
		}
	];

	let selectedPreset = $state<string>('s1_ptn');
	let presentCost = $state<number>(80_000_000);
	let horizonYears = $state<number>(12);
	let eduInflationPct = $state<number>(10.0); // Riset Kemendikbud & BPS: inflasi pendidikan 10-15%/th
	let expectedReturnPct = $state<number>(7.0); // Portofolio moderat SBN / Reksadana Campuran

	function applyPreset(presetId: string) {
		selectedPreset = presetId;
		const found = EDU_PRESETS.find((p) => p.id === presetId);
		if (found) {
			presentCost = found.defaultCost;
			horizonYears = found.defaultYears;
		}
	}

	// Nilai masa depan dana pendidikan (Future Value)
	let futureCost = $derived(
		presentCost * Math.pow(1 + eduInflationPct / 100, Math.max(1, horizonYears))
	);

	// Kebutuhan tabungan/investasi bulanan (PMT)
	let monthlySavingsNeeded = $derived.by(() => {
		const n = Math.max(1, horizonYears) * 12;
		const r = expectedReturnPct / 100 / 12;
		if (r <= 0) return futureCost / n;
		return (futureCost * r) / (Math.pow(1 + r, n) - 1);
	});

	// Perbandingan kesiapan dana pendidikan antar kembaran digital
	let twinReadiness = $derived.by(() => {
		const targetYear = Math.min(Math.max(1, horizonYears), 20);
		return twins.map((t) => {
			const pt =
				t.yearly_series.find((p) => p.year === targetYear) ??
				t.yearly_series[t.yearly_series.length - 1];
			const invest = pt?.invest ?? 0;
			const cash = pt?.cash ?? 0;
			const totalLiquid = invest + cash;
			const readinessPct = futureCost > 0 ? (invest / futureCost) * 100 : 100;
			const gap = invest - futureCost;

			return {
				twin: t,
				targetYear,
				invest,
				cash,
				totalLiquid,
				readinessPct,
				gap,
				isFullyFunded: gap >= 0
			};
		});
	});
</script>

<div class="card space-y-5 p-5">
	<div
		class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4"
	>
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🎓</span>
				<h3 class="font-bold">Perencana Dana Pendidikan Anak Multiverse</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Simulasi lonjakan biaya sekolah/kuliah dengan inflasi pendidikan khusus (BPS: 10–15%/th) vs
				portofolio kembaranmu.
			</p>
		</div>
		<span class="chip border-indigo-500/40 bg-indigo-500/10 text-xs font-medium text-indigo-300">
			Kemendikbud & BPS Benchmark
		</span>
	</div>

	<!-- Pemilihan Preset Jenjang Pendidikan -->
	<div>
		<span class="mb-2 block text-xs font-semibold text-[var(--color-ink)]">
			Pilih Target Jenjang Pendidikan
		</span>
		<div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
			{#each EDU_PRESETS as p}
				<button
					type="button"
					class="flex flex-col items-start rounded-xl border p-2.5 text-left transition {selectedPreset ===
					p.id
						? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-[var(--color-ink)]'
						: 'border-[var(--color-line)] bg-[var(--color-void-2)] hover:border-slate-600'}"
					onclick={() => applyPreset(p.id)}
				>
					<div class="flex items-center gap-1.5 font-semibold text-xs">
						<span>{p.icon}</span>
						<span>{p.label}</span>
					</div>
					<span class="mt-1 text-[11px] text-[var(--color-ink-dim)]">{p.sub}</span>
					<span class="mt-1.5 font-mono text-xs font-bold text-[var(--color-accent)]">
						{rupiahBrief(p.defaultCost)} (th-{p.defaultYears})
					</span>
				</button>
			{/each}
		</div>
	</div>

	<!-- Parameter Interaktif -->
	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<label
				for="edu-present-cost"
				class="block text-[11px] font-medium text-[var(--color-ink-dim)]"
			>
				Estimasi Biaya Saat Ini (PV)
			</label>
			<input
				id="edu-present-cost"
				type="number"
				step="5000000"
				min="5000000"
				max="2000000000"
				bind:value={presentCost}
				class="mt-1.5 w-full rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] px-3 py-1.5 font-mono text-sm text-[var(--color-ink)]"
			/>
			<span class="mt-1 block text-right font-mono text-[11px] text-[var(--color-accent)]">
				{rupiah(presentCost)}
			</span>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<div
				class="flex items-center justify-between text-[11px] font-medium text-[var(--color-ink-dim)]"
			>
				<span>Waktu Menuju Masuk</span>
				<span class="font-mono font-bold text-[var(--color-ink)]">{horizonYears} Tahun</span>
			</div>
			<input
				type="range"
				min="1"
				max="18"
				step="1"
				bind:value={horizonYears}
				class="mt-3 w-full accent-[var(--color-accent)]"
			/>
			<span class="mt-1 block text-[10px] text-[var(--color-ink-dim)]">
				{horizonYears * 12} bulan akumulasi investasi
			</span>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<div
				class="flex items-center justify-between text-[11px] font-medium text-[var(--color-ink-dim)]"
			>
				<span>Inflasi Pendidikan / Th</span>
				<span class="font-mono font-bold text-amber-400">{eduInflationPct.toFixed(1)}%</span>
			</div>
			<input
				type="range"
				min="5.0"
				max="18.0"
				step="0.5"
				bind:value={eduInflationPct}
				class="mt-3 w-full accent-amber-500"
			/>
			<span class="mt-1 block text-[10px] text-[var(--color-ink-dim)]">
				BPS: Rata-rata 10–12% per tahun
			</span>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<div
				class="flex items-center justify-between text-[11px] font-medium text-[var(--color-ink-dim)]"
			>
				<span>Asumsi Return Investasi</span>
				<span class="font-mono font-bold text-emerald-400">{expectedReturnPct.toFixed(1)}%</span>
			</div>
			<input
				type="range"
				min="3.0"
				max="14.0"
				step="0.5"
				bind:value={expectedReturnPct}
				class="mt-3 w-full accent-emerald-500"
			/>
			<span class="mt-1 block text-[10px] text-[var(--color-ink-dim)]">
				Portofolio moderat (SBN + Reksadana)
			</span>
		</div>
	</div>

	<!-- Ringkasan Target FV & Investasi Bulanan -->
	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
		<div class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
			<div class="flex items-center justify-between">
				<span class="text-xs font-semibold text-amber-300">Target Biaya Masa Depan (FV)</span>
				<span class="text-xs">📈</span>
			</div>
			<div class="mt-2 text-2xl font-black font-mono text-amber-400">
				{rupiah(futureCost)}
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Naik <strong>{(futureCost / presentCost).toFixed(1)}× lipat</strong> dari {rupiahBrief(
					presentCost
				)} dalam {horizonYears} tahun ke depan akibat inflasi pendidikan {eduInflationPct}%.
			</p>
		</div>

		<div class="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
			<div class="flex items-center justify-between">
				<span class="text-xs font-semibold text-emerald-300"
					>Investasi Rutin Bulanan Diperlukan</span
				>
				<span class="text-xs">💰</span>
			</div>
			<div class="mt-2 text-2xl font-black font-mono text-emerald-400">
				{rupiah(monthlySavingsNeeded)}<span class="text-xs font-normal text-emerald-300">/bln</span>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Alokasi autodebet per bulan di instrumen berimbal hasil {expectedReturnPct}% per tahun
				selama {horizonYears}
				tahun.
			</p>
		</div>
	</div>

	<!-- Analisis Kesiapan Antarkembar Multiverse -->
	<div class="space-y-3">
		<h4 class="text-xs font-semibold text-[var(--color-ink)]">
			Kesiapan Portofolio Investasi Kembaran Digital (Tahun ke-{horizonYears})
		</h4>
		<div class="space-y-2.5">
			{#each twinReadiness as tr (tr.twin.code)}
				<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3.5">
					<div class="flex flex-wrap items-center justify-between gap-2">
						<div class="flex items-center gap-2">
							<span
								class="inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold"
								style="background: {tr.twin.color}20; color: {tr.twin.color};"
							>
								{twinIcon(tr.twin.icon)}
							</span>
							<div>
								<span class="font-bold text-xs">{tr.twin.label}</span>
								<span class="ml-1 text-[11px] text-[var(--color-ink-dim)]">({tr.twin.code})</span>
							</div>
						</div>

						<div class="flex items-center gap-2">
							{#if tr.isFullyFunded}
								<span
									class="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/30"
								>
									✓ Siap Terpenuhi (Surplus {rupiahBrief(tr.gap)})
								</span>
							{:else}
								<span
									class="rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-semibold text-rose-400 border border-rose-500/30"
								>
									⚠ Defisit {rupiahBrief(Math.abs(tr.gap))}
								</span>
							{/if}
							<span class="font-mono text-xs font-bold text-[var(--color-ink)]">
								{percent(tr.readinessPct / 100, 0)}
							</span>
						</div>
					</div>

					<!-- Progress bar visual kesiapan -->
					<div class="mt-2.5 h-2 w-full overflow-hidden rounded-full bg-[var(--color-void-3)]">
						<div
							class="h-full rounded-full transition-all duration-500"
							style="width: {Math.min(
								100,
								Math.max(0, tr.readinessPct)
							)}%; background: {tr.isFullyFunded ? '#10B981' : tr.twin.color};"
						></div>
					</div>

					<div
						class="mt-2 flex items-center justify-between text-[11px] text-[var(--color-ink-dim)]"
					>
						<span>
							Saldo Investasi: <strong class="font-mono text-[var(--color-ink)]"
								>{rupiah(tr.invest)}</strong
							>
						</span>
						<span>
							Target FV: <strong class="font-mono text-[var(--color-ink)]"
								>{rupiahBrief(futureCost)}</strong
							>
						</span>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- Tips Edukasi Glide Path & Perpajakan -->
	<div
		class="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-4 text-xs text-[var(--color-ink-dim)]"
	>
		<div class="flex items-center gap-2 font-semibold text-indigo-300">
			<span>💡</span>
			<span>Strategi Siklus Hidup Portofolio Anak (Glide Path Derisking)</span>
		</div>
		<ul class="mt-2 list-inside list-disc space-y-1">
			<li>
				<strong>Horizon Panjang (&gt; 5 Tahun):</strong> Porsi agresif di Reksadana Indeks / Saham untuk
				melawan laju inflasi pendidikan 10–12%.
			</li>
			<li>
				<strong>Horizon Pendek (&lt; 3 Tahun):</strong> Lakukan <em>derisking</em> bertahap ke SBN Ritel
				(ORI/SR) atau Reksadana Pasar Uang agar pokok dana tidak tergerus volatilitas pasar saat pendaftaran.
			</li>
			<li>
				<strong>Efisiensi Pajak:</strong> Imbal hasil SBN ritel hanya dikenakan PPh Final 10% (lebih hemat
				dibanding deposito 20%), dan reksadana bukan objek pajak (UU HPP).
			</li>
		</ul>
	</div>
</div>
