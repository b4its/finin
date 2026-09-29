<script lang="ts">
	import type { Twin, Profile } from '$lib/api/types';
	import { rupiah, rupiahBrief } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	interface Props {
		twins: Twin[];
		profile?: Profile;
	}

	let { twins, profile }: Props = $props();

	let evaluationYear = $state<number>(3);
	let austerityCutPct = $state<number>(20); // Penghematan darurat pengeluaran gaya hidup (%)
	let includeJKP = $state<boolean>(true); // Jaminan Kehilangan Pekerjaan (PP 37/2021)

	// Plafon upah maksimal JKP BPJS Ketenagakerjaan (Rp 5.000.000)
	const JKP_MAX_WAGE = 5_000_000;
	let userWage = $derived(profile?.income_monthly ?? 10_000_000);
	let jkpWageBase = $derived(Math.min(userWage, JKP_MAX_WAGE));
	let jkpBenefitMonth1To3 = $derived(jkpWageBase * 0.45); // 45% upah di 3 bulan pertama
	let jkpBenefitMonth4To6 = $derived(jkpWageBase * 0.25); // 25% upah di 3 bulan berikutnya

	interface TwinRunway {
		twin: Twin;
		cashReserve: number;
		investReserve: number;
		totalLiquid: number;
		monthlyLiving: number;
		monthlyDebt: number;
		monthlyFamily: number;
		totalBurnRate: number;
		runwayMonths: number;
		safetyStatus: 'critical' | 'moderate' | 'ideal' | 'fortress';
	}

	let twinRunways = $derived.by<TwinRunway[]>(() => {
		const targetYear = Math.min(Math.max(1, evaluationYear), 20);
		const baseExpense = profile?.expense_monthly ?? 5_000_000;
		const dependents = profile?.dependents_monthly ?? 0;

		return twins.map((t) => {
			const pt =
				t.yearly_series.find((p) => p.year === targetYear) ??
				t.yearly_series[t.yearly_series.length - 1];

			// Pengeluaran di tahun tersebut dengan estimasi inflasi 3% per tahun
			const inflationFactor = Math.pow(1.03, targetYear);
			const livingCostInflated = baseExpense * inflationFactor * (1 - austerityCutPct / 100);
			const familyCostInflated = dependents * inflationFactor;
			// Estimasi cicilan utang bulanan jika ada sisa debt
			const debtRemaining = pt?.debt ?? 0;
			const monthlyDebt =
				debtRemaining > 0
					? Math.min(debtRemaining, profile?.existing_debt?.monthly_payment ?? 0)
					: 0;
			const totalBurn = Math.max(1_000_000, livingCostInflated + familyCostInflated + monthlyDebt);

			const cash = pt?.cash ?? 0;
			// Hanya aset pasar modal yang likuid cepat; properti/kendaraan TIDAK
			// boleh dihitung sebagai kas darurat. `pt.invest` = pasar + aset riil,
			// jadi pakai komponen pasar (fallback: kurangi aset riil).
			const propertyValue = pt?.property_value ?? 0;
			const vehicleValue = pt?.vehicle_value ?? 0;
			const marketInvest =
				pt?.market_invest ??
				Math.max(0, Math.max(0, pt?.invest ?? 0) - propertyValue - vehicleValue);
			// Kas likuid utama + 30% alokasi instrumen pasar uang yang dapat dicairkan kilat tanpa penalti
			const totalLiquid = Math.max(0, cash + marketInvest * 0.3);

			// Simulasi runway bulan demi bulan dengan memperhitungkan subsidi JKP jika aktif
			let remainingCash = totalLiquid;
			let monthsSurvived = 0;
			for (let month = 1; month <= 60; month++) {
				let subsidy = 0;
				if (includeJKP) {
					if (month <= 3) subsidy = jkpBenefitMonth1To3;
					else if (month <= 6) subsidy = jkpBenefitMonth4To6;
				}
				const netBurn = Math.max(500_000, totalBurn - subsidy);
				if (remainingCash >= netBurn) {
					remainingCash -= netBurn;
					monthsSurvived += 1;
				} else {
					monthsSurvived += remainingCash / netBurn;
					break;
				}
			}

			let safetyStatus: 'critical' | 'moderate' | 'ideal' | 'fortress' = 'moderate';
			if (monthsSurvived < 3) safetyStatus = 'critical';
			else if (monthsSurvived < 6) safetyStatus = 'moderate';
			else if (monthsSurvived < 12) safetyStatus = 'ideal';
			else safetyStatus = 'fortress';

			return {
				twin: t,
				cashReserve: cash,
				investReserve: marketInvest,
				totalLiquid,
				monthlyLiving: livingCostInflated,
				monthlyDebt,
				monthlyFamily: familyCostInflated,
				totalBurnRate: totalBurn,
				runwayMonths: monthsSurvived,
				safetyStatus
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
				<span class="text-xl">🛡️</span>
				<h3 class="font-bold">Simulasi Ketahanan Kas & Runway Likuiditas Darurat</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Uji ketahanan likuiditas jika penghasilan terhenti total (PHK / guncangan usaha) pada tahun
				ke-{evaluationYear}.
			</p>
		</div>
		<span class="chip border-emerald-500/40 bg-emerald-500/10 text-xs font-medium text-emerald-300">
			PP 37/2021 JKP & Standar OJK
		</span>
	</div>

	<!-- Parameter Interaktif -->
	<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<div
				class="flex items-center justify-between text-[11px] font-medium text-[var(--color-ink-dim)]"
			>
				<span>Tahun Terjadinya Guncangan</span>
				<span class="font-mono font-bold text-[var(--color-ink)]">Tahun ke-{evaluationYear}</span>
			</div>
			<input
				type="range"
				min="1"
				max="15"
				step="1"
				bind:value={evaluationYear}
				class="mt-3 w-full accent-[var(--color-accent)]"
			/>
			<span class="mt-1 block text-[10px] text-[var(--color-ink-dim)]">
				Bulan ke-{evaluationYear * 12} dari awal simulasi
			</span>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<div
				class="flex items-center justify-between text-[11px] font-medium text-[var(--color-ink-dim)]"
			>
				<span>Pemotongan Pengeluaran Gaya Hidup</span>
				<span class="font-mono font-bold text-amber-400">-{austerityCutPct}%</span>
			</div>
			<input
				type="range"
				min="0"
				max="50"
				step="5"
				bind:value={austerityCutPct}
				class="mt-3 w-full accent-amber-500"
			/>
			<span class="mt-1 block text-[10px] text-[var(--color-ink-dim)]">
				Efisiensi pos jajan & langganan darurat
			</span>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<div
				class="flex items-center justify-between text-[11px] font-medium text-[var(--color-ink-dim)]"
			>
				<span>Manfaat JKP BPJS TK</span>
				<span class="font-mono font-bold text-sky-400">{includeJKP ? 'Aktif' : 'Nonaktif'}</span>
			</div>
			<label class="mt-2.5 flex cursor-pointer items-center gap-2 text-xs">
				<input type="checkbox" bind:checked={includeJKP} class="h-4 w-4 rounded accent-sky-500" />
				<span class="text-[11px] text-[var(--color-ink)]">Klaim subsidi tunai 6 bulan</span>
			</label>
			<span class="mt-1 block text-[10px] text-[var(--color-ink-dim)]">
				Maks Rp{rupiahBrief(jkpBenefitMonth1To3)}/bln (bln 1-3) & Rp{rupiahBrief(
					jkpBenefitMonth4To6
				)}/bln (bln 4-6)
			</span>
		</div>
	</div>

	<!-- Barometer Standar Acuan OJK / Kemenkeu -->
	<div class="grid grid-cols-2 gap-2 sm:grid-cols-4 text-center">
		<div class="rounded-xl border border-rose-500/20 bg-rose-500/5 p-2.5">
			<span class="block text-[10px] font-semibold text-rose-400">&lt; 3 Bulan</span>
			<span class="text-[11px] font-bold text-[var(--color-ink)]">🔴 Kritis</span>
			<span class="mt-0.5 block text-[9px] text-[var(--color-ink-dim)]"
				>Risiko kredit macet OJK</span
			>
		</div>
		<div class="rounded-xl border border-amber-500/20 bg-amber-500/5 p-2.5">
			<span class="block text-[10px] font-semibold text-amber-400">3 – 6 Bulan</span>
			<span class="text-[11px] font-bold text-[var(--color-ink)]">🟡 Cukup</span>
			<span class="mt-0.5 block text-[9px] text-[var(--color-ink-dim)]"
				>Standar lajang & karyawan</span
			>
		</div>
		<div class="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-2.5">
			<span class="block text-[10px] font-semibold text-emerald-400">6 – 12 Bulan</span>
			<span class="text-[11px] font-bold text-[var(--color-ink)]">🟢 Ideal</span>
			<span class="mt-0.5 block text-[9px] text-[var(--color-ink-dim)]">Keluarga & freelancer</span>
		</div>
		<div class="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-2.5">
			<span class="block text-[10px] font-semibold text-indigo-400">&gt; 12 Bulan</span>
			<span class="text-[11px] font-bold text-[var(--color-ink)]">💎 Benteng Finansial</span>
			<span class="mt-0.5 block text-[9px] text-[var(--color-ink-dim)]">Kebal krisis ekonomi</span>
		</div>
	</div>

	<!-- Perbandingan Runway Antarkembar -->
	<div class="space-y-3">
		<h4 class="text-xs font-semibold text-[var(--color-ink)]">
			Daya Tahan Kelangsungan Hidup (Runway Bertahan Tanpa Utang Baru)
		</h4>
		<div class="space-y-2.5">
			{#each twinRunways as tr (tr.twin.code)}
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
							{#if tr.safetyStatus === 'critical'}
								<span
									class="rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-400 border border-rose-500/30"
								>
									🔴 Rentan Gagal Bayar
								</span>
							{:else if tr.safetyStatus === 'moderate'}
								<span
									class="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-bold text-amber-400 border border-amber-500/30"
								>
									🟡 Cukup Singkat
								</span>
							{:else if tr.safetyStatus === 'ideal'}
								<span
									class="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/30"
								>
									🟢 Zona Aman OJK
								</span>
							{:else}
								<span
									class="rounded-full bg-indigo-500/20 px-2 py-0.5 text-[10px] font-bold text-indigo-400 border border-indigo-500/30"
								>
									💎 Sangat Tangguh
								</span>
							{/if}
							<span class="font-mono text-sm font-black text-[var(--color-ink)]">
								{tr.runwayMonths.toFixed(1)} Bulan
							</span>
						</div>
					</div>

					<!-- Visual Bar Runway -->
					<div
						class="relative mt-2.5 h-3 w-full overflow-hidden rounded-full bg-[var(--color-void-3)]"
					>
						<!-- Target line 6 bulan (50% dari 12 bln scale) -->
						<div
							class="absolute top-0 bottom-0 z-10 w-0.5 bg-emerald-400/80"
							style="left: 50%;"
							title="Batas Ideal OJK: 6 Bulan"
						></div>
						<div
							class="h-full rounded-full transition-all duration-500"
							style="width: {Math.min(
								100,
								Math.max(3, (tr.runwayMonths / 12) * 100)
							)}%; background: {tr.safetyStatus === 'critical'
								? '#F43F5E'
								: tr.safetyStatus === 'moderate'
									? '#F59E0B'
									: tr.safetyStatus === 'ideal'
										? '#10B981'
										: '#6366F1'};"
						></div>
					</div>

					<div
						class="mt-2 flex flex-wrap items-center justify-between gap-2 text-[11px] text-[var(--color-ink-dim)]"
					>
						<span>
							Likuiditas Siaga: <strong class="font-mono text-[var(--color-ink)]"
								>{rupiahBrief(tr.totalLiquid)}</strong
							>
							(Kas {rupiahBrief(tr.cashReserve)} + Pasar Uang {rupiahBrief(tr.investReserve * 0.3)})
						</span>
						<span>
							Beban Pengeluaran: <strong class="font-mono text-rose-300"
								>{rupiah(tr.totalBurnRate)}/bln</strong
							>
							{#if tr.monthlyDebt > 0}
								(termasuk cicilan {rupiahBrief(tr.monthlyDebt)})
							{/if}
						</span>
					</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- Panduan Aksi Darurat -->
	<div
		class="rounded-xl border border-sky-500/20 bg-sky-500/5 p-4 text-xs text-[var(--color-ink-dim)]"
	>
		<div class="flex items-center gap-2 font-semibold text-sky-300">
			<span>📌</span>
			<span>Protokol Keuangan Saat Terkena Guncangan Pendapatan</span>
		</div>
		<div class="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-3">
			<div class="rounded-lg bg-[var(--color-void-2)] p-2">
				<strong class="text-[var(--color-ink)] block">1. Klaim JKP BPJS Segera</strong>
				Laporkan status PHK melalui portal SiapKerja Kemnaker dalam 3 bulan agar hak uang tunai tidak
				hangus.
			</div>
			<div class="rounded-lg bg-[var(--color-void-2)] p-2">
				<strong class="text-[var(--color-ink)] block">2. Komunikasi Restrukturisasi</strong>
				Ajukan permohonan restrukturisasi cicilan ke bank/leasing sebelum jatuh tempo agar skor SLIK OJK
				tidak anjlok.
			</div>
			<div class="rounded-lg bg-[var(--color-void-2)] p-2">
				<strong class="text-[var(--color-ink)] block">3. Cairkan Bertahap</strong>
				Cairkan kas tabungan dulu, lalu reksadana pasar uang. Hindari mencairkan saham yang sedang dalam
				kondisi minus (*floating loss*).
			</div>
		</div>
	</div>
</div>
