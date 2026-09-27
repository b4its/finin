<script lang="ts">
	import type { Twin, Profile } from '$lib/api/types';
	import { rupiah, rupiahBrief, percent } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let { twins, profile }: { twins: Twin[]; profile: Profile } = $props();

	// Usia dasar pengguna
	let currentAge = $derived(profile?.age || 28);

	// Target Usia Pensiun (Default usia normal Permenaker 4/2022: 56 tahun)
	let targetRetirementAge = $state(55);
	let fireMode = $state<'lean' | 'standard' | 'fat'>('standard');

	// Asumsi SBN / Dividen Yield Riil Bersih Pajak di Indonesia (5.0%)
	const safeWithdrawalRate = 0.05;
	const inflationAnnual = 0.035;

	// Pengeluaran bulanan saat ini
	let baseMonthlyExpense = $derived(
		(profile?.expense_monthly || 5_000_000) + (profile?.dependents_monthly || 0)
	);

	// Multiplier gaya hidup FIRE
	let expenseMultiplier = $derived(fireMode === 'lean' ? 0.7 : fireMode === 'fat' ? 1.4 : 1.0);

	// Tahun menuju pensiun
	let yearsToRetire = $derived(Math.max(1, targetRetirementAge - currentAge));

	// Pengeluaran bulanan di usia pensiun setelah inflasi
	let monthlyExpenseAtRetirement = $derived(
		baseMonthlyExpense * expenseMultiplier * Math.pow(1 + inflationAnnual, yearsToRetire)
	);

	let annualExpenseAtRetirement = $derived(monthlyExpenseAtRetirement * 12);

	// Target Angka FIRE (FIRE Number) di usia pensiun
	let fireTargetNetWorth = $derived(annualExpenseAtRetirement / safeWithdrawalRate);

	// Estimasi JHT BPJS Ketenagakerjaan (5.7% per bulan, rata-rata yield 6% per tahun)
	let estimatedJhtAtRetirement = $derived.by(() => {
		if (profile.income_type !== 'salary') return 0;
		const monthlyGross = profile.income_monthly || 0;
		const monthlyContribution = monthlyGross * 0.057; // 2% pekerja + 3.7% pemberi kerja
		const monthlyRate = Math.pow(1.06, 1 / 12) - 1;
		let total = 0;
		const totalMonths = yearsToRetire * 12;
		for (let m = 0; m < totalMonths; m++) {
			total = (total + monthlyContribution) * (1 + monthlyRate);
		}
		return Math.round(total);
	});

	// Analisis tiap twin
	let twinAnalysis = $derived(
		twins.map((t) => {
			// Cari tahun pertama saat net worth mencapai fireTargetNetWorth (pada nominal tahun tersebut)
			let fireAchievedYear: number | null = null;
			let fireAchievedAge: number | null = null;

			for (const pt of t.yearly_series) {
				const expAtPtYear =
					baseMonthlyExpense * expenseMultiplier * Math.pow(1 + inflationAnnual, pt.year);
				const targetAtPtYear = (expAtPtYear * 12) / safeWithdrawalRate;
				if (pt.net_worth >= targetAtPtYear) {
					fireAchievedYear = pt.year;
					fireAchievedAge = currentAge + pt.year;
					break;
				}
			}

			// Ambil snapshot pada target tahun pensiun (atau data terakhir yang ada)
			const ptAtRetire =
				t.yearly_series.find((p) => p.year === yearsToRetire) ??
				t.yearly_series[Math.min(yearsToRetire, t.yearly_series.length - 1)];

			const nwAtRetirement = ptAtRetire ? ptAtRetire.net_worth : 0;
			// Total dana pensiun (Aset mandiri + saldo JHT BPJS)
			const totalRetirementAssets = nwAtRetirement + estimatedJhtAtRetirement;

			// Passive income bulanan dari kupon SBN / dividen saham (5% riil / 12)
			const monthlyPassiveCashflow = (totalRetirementAssets * safeWithdrawalRate) / 12;

			// Coverage ratio terhadap pengeluaran pensiun
			const coverageRatio =
				monthlyExpenseAtRetirement > 0 ? monthlyPassiveCashflow / monthlyExpenseAtRetirement : 1.0;

			const isFunded = coverageRatio >= 1.0;

			return {
				code: t.code,
				label: t.label,
				color: t.color,
				icon: t.icon,
				fireAchievedYear,
				fireAchievedAge,
				nwAtRetirement,
				totalRetirementAssets,
				monthlyPassiveCashflow,
				coverageRatio,
				isFunded
			};
		})
	);
</script>

<div class="card p-5">
	<div
		class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4"
	>
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🌅</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Kalkulator Kesiapan Pensiun & FIRE (Financial Independence)
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Evaluasi kapan tiap Twin mencapai kemandirian finansial dan proyeksi arus kas pasif hari tua
				berbanding acuan Permenaker 4/2022 (Usia 56 Th).
			</p>
		</div>

		<div class="flex flex-wrap items-center gap-3">
			<!-- Pilihan Tipe FIRE -->
			<div
				class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs"
			>
				<button
					class="rounded-md px-2.5 py-1 font-semibold transition {fireMode === 'lean'
						? 'bg-[var(--color-accent)] text-white'
						: 'text-[var(--color-ink-dim)]'}"
					onclick={() => (fireMode = 'lean')}
				>
					Lean (70%)
				</button>
				<button
					class="rounded-md px-2.5 py-1 font-semibold transition {fireMode === 'standard'
						? 'bg-[var(--color-accent)] text-white'
						: 'text-[var(--color-ink-dim)]'}"
					onclick={() => (fireMode = 'standard')}
				>
					Standar (100%)
				</button>
				<button
					class="rounded-md px-2.5 py-1 font-semibold transition {fireMode === 'fat'
						? 'bg-[var(--color-accent)] text-white'
						: 'text-[var(--color-ink-dim)]'}"
					onclick={() => (fireMode = 'fat')}
				>
					Fat FIRE (140%)
				</button>
			</div>
		</div>
	</div>

	<!-- Slider Target Usia Pensiun -->
	<div class="mt-4 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-4">
		<div class="flex flex-wrap items-center justify-between gap-2 text-xs">
			<div>
				<span class="font-bold text-[var(--color-ink)]">Target Usia Pensiun Anda:</span>
				<span class="ml-1.5 font-extrabold text-[var(--color-accent)]"
					>{targetRetirementAge} Tahun</span
				>
				<span class="text-[var(--color-ink-dim)]"
					>({yearsToRetire} tahun lagi dari usia saat ini {currentAge} th)</span
				>
			</div>
			<div class="flex items-center gap-2">
				{#each [45, 50, 55, 60] as age}
					<button
						class="rounded-md border border-[var(--color-line)] px-2 py-0.5 text-[11px] font-semibold transition hover:border-[var(--color-accent)] {targetRetirementAge ===
						age
							? 'bg-[var(--color-accent)] text-white'
							: 'bg-[var(--color-void-2)] text-[var(--color-ink-dim)]'}"
						onclick={() => (targetRetirementAge = age)}
					>
						Usia {age}
					</button>
				{/each}
			</div>
		</div>

		<div class="mt-2.5">
			<input
				type="range"
				min="40"
				max="65"
				step="1"
				bind:value={targetRetirementAge}
				class="w-full accent-[var(--color-accent)] cursor-pointer"
			/>
		</div>

		<!-- Metrik Kebutuhan Finansial -->
		<div
			class="mt-3 grid grid-cols-1 gap-2.5 sm:grid-cols-3 text-xs border-t border-[var(--color-line)] pt-3"
		>
			<div class="flex justify-between sm:flex-col sm:justify-start">
				<span class="text-[var(--color-ink-dim)]">Pengeluaran Hari Tua:</span>
				<strong class="text-[var(--color-ink)]">{rupiah(monthlyExpenseAtRetirement)}/bln</strong>
			</div>
			<div class="flex justify-between sm:flex-col sm:justify-start">
				<span class="text-[var(--color-ink-dim)]">Angka FIRE Bebas Finansial:</span>
				<strong class="text-amber-400">{rupiah(fireTargetNetWorth)}</strong>
			</div>
			<div class="flex justify-between sm:flex-col sm:justify-start">
				<span class="text-[var(--color-ink-dim)]">Akumulasi JHT BPJS (Klaim 56 Th):</span>
				<strong class="text-emerald-400">+{rupiah(estimatedJhtAtRetirement)}</strong>
			</div>
		</div>
	</div>

	<!-- Kartu Tiap Twin -->
	<div class="mt-4 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
		{#each twinAnalysis as st (st.code)}
			<div
				class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4 flex flex-col justify-between"
				style="border-top: 3px solid {st.color};"
			>
				<div>
					<div class="flex items-center justify-between">
						<span class="flex items-center gap-1.5 text-xs font-bold text-[var(--color-ink)]">
							<span>{twinIcon(st.icon)}</span>
							Twin {st.code}: {st.label}
						</span>
						<span
							class="rounded-full px-2 py-0.5 text-[10px] font-bold {st.isFunded
								? 'bg-emerald-500/15 text-emerald-400'
								: 'bg-rose-500/15 text-rose-400'}"
						>
							{percent(st.coverageRatio, 0)} Aman
						</span>
					</div>

					<div class="mt-3 space-y-2 text-xs">
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>Capaian Bebas Finansial:</span>
							{#if st.fireAchievedAge}
								<strong class="text-emerald-400">
									Usia {st.fireAchievedAge} Th (Th-{st.fireAchievedYear}) 🚀
								</strong>
							{:else}
								<span class="text-slate-400 font-medium">Belum pada horison ini</span>
							{/if}
						</div>

						<div
							class="flex justify-between text-[var(--color-ink-dim)] border-t border-dashed border-[var(--color-line)] pt-1.5"
						>
							<span>Total Aset di Usia {targetRetirementAge}:</span>
							<strong class="text-[var(--color-ink)]"
								>{rupiahBrief(st.totalRetirementAssets)}</strong
							>
						</div>

						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>Passive Income / Bulan:</span>
							<strong class={st.isFunded ? 'text-emerald-400' : 'text-amber-400'}>
								{rupiah(st.monthlyPassiveCashflow)}/bln
							</strong>
						</div>

						<div
							class="flex justify-between text-[var(--color-ink-dim)] border-t border-dashed border-[var(--color-line)] pt-1.5"
						>
							<span>Status Arus Kas:</span>
							<span class="font-semibold {st.isFunded ? 'text-emerald-400' : 'text-rose-400'}">
								{st.isFunded ? '✓ Mandiri Finansial Penuh' : '⚠️ Defisit vs Pengeluaran'}
							</span>
						</div>
					</div>
				</div>

				<div
					class="mt-3 border-t border-[var(--color-line)]/50 pt-2 text-[10px] text-[var(--color-ink-dim)]"
				>
					{#if st.isFunded}
						<span
							>✨ Portofolio aset dan jaminan sosial cukup untuk mendanai gaya hidup pensiun tanpa
							harus bekerja aktif.</span
						>
					{:else}
						<span
							>Tingkatkan alokasi investasi bulanan atau tunda usia pensiun untuk menutup selisih
							pengeluaran.</span
						>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>
