<script lang="ts">
	import { rupiah, rupiahBrief, percent } from '$lib/utils/format';
	import CurrencyInput from '$lib/components/ui/CurrencyInput.svelte';

	let { initialGross = 10_000_000 }: { initialGross?: number } = $props();

	let grossMonthly = $state(0);
	$effect(() => {
		if (grossMonthly === 0 && initialGross > 0) {
			grossMonthly = initialGross;
		}
	});
	let terCategory = $state<'A' | 'B' | 'C'>('A');
	let includeBpjs = $state(true);
	let currentAge = $state(26);

	// Tabel TER A, B, C client-side untuk responsivitas instan
	const TER_A_LIMITS: [number, number][] = [
		[5_400_000, 0.0],
		[5_650_000, 0.0025],
		[5_950_000, 0.005],
		[6_300_000, 0.0075],
		[6_750_000, 0.01],
		[7_500_000, 0.0125],
		[8_550_000, 0.015],
		[9_650_000, 0.0175],
		[10_050_000, 0.02],
		[10_350_000, 0.0225],
		[10_700_000, 0.025],
		[11_050_000, 0.03],
		[11_600_000, 0.035],
		[12_500_000, 0.04],
		[13_750_000, 0.05],
		[15_100_000, 0.06],
		[16_950_000, 0.07],
		[19_750_000, 0.08],
		[24_150_000, 0.09],
		[26_450_000, 0.1],
		[28_000_000, 0.11],
		[30_050_000, 0.12],
		[32_400_000, 0.13],
		[35_400_000, 0.14],
		[39_100_000, 0.15],
		[43_850_000, 0.16],
		[47_800_000, 0.17],
		[51_400_000, 0.18],
		[56_300_000, 0.19],
		[62_200_000, 0.2],
		[Infinity, 0.25]
	];

	const TER_B_LIMITS: [number, number][] = [
		[6_200_000, 0.0],
		[6_500_000, 0.0025],
		[6_850_000, 0.005],
		[7_300_000, 0.0075],
		[9_200_000, 0.01],
		[10_750_000, 0.015],
		[11_250_000, 0.02],
		[11_600_000, 0.025],
		[12_600_000, 0.03],
		[13_600_000, 0.04],
		[14_950_000, 0.05],
		[16_400_000, 0.06],
		[18_450_000, 0.07],
		[21_850_000, 0.08],
		[26_000_000, 0.09],
		[Infinity, 0.25]
	];

	const TER_C_LIMITS: [number, number][] = [
		[6_600_000, 0.0],
		[6_950_000, 0.0025],
		[7_350_000, 0.005],
		[7_800_000, 0.0075],
		[8_850_000, 0.01],
		[9_800_000, 0.0125],
		[10_950_000, 0.015],
		[11_200_000, 0.0175],
		[12_050_000, 0.02],
		[12_950_000, 0.03],
		[14_150_000, 0.04],
		[15_550_000, 0.05],
		[Infinity, 0.25]
	];

	function getRate(gross: number, cat: 'A' | 'B' | 'C'): number {
		const limits = cat === 'A' ? TER_A_LIMITS : cat === 'B' ? TER_B_LIMITS : TER_C_LIMITS;
		for (const [limit, rate] of limits) {
			if (gross <= limit) return rate;
		}
		return 0.3;
	}

	let terRate = $derived(getRate(grossMonthly, terCategory));
	let pph21 = $derived(Math.round(grossMonthly * terRate));

	const JP_MAX_WAGE = 10_042_300;
	const KES_MAX_WAGE = 12_000_000;

	let jhtWorker = $derived(includeBpjs ? Math.round(grossMonthly * 0.02) : 0);
	let jpWorker = $derived(includeBpjs ? Math.round(Math.min(grossMonthly, JP_MAX_WAGE) * 0.01) : 0);
	let kesWorker = $derived(
		includeBpjs ? Math.round(Math.min(grossMonthly, KES_MAX_WAGE) * 0.01) : 0
	);

	let jhtEmployer = $derived(includeBpjs ? Math.round(grossMonthly * 0.037) : 0);
	let totalJhtMonthly = $derived(jhtWorker + jhtEmployer);

	let totalDeductions = $derived(pph21 + jhtWorker + jpWorker + kesWorker);
	let netTakeHomePay = $derived(Math.max(0, grossMonthly - totalDeductions));

	// Proyeksi JHT 56 tahun
	let yearsToPension = $derived(Math.max(1, 56 - currentAge));
	let projectedJhtLumpSum = $derived.by(() => {
		const r = Math.pow(1 + 0.056, 1 / 12) - 1;
		let balance = 0;
		let monthlyContribution = totalJhtMonthly;
		for (let y = 0; y < yearsToPension; y++) {
			for (let m = 0; m < 12; m++) {
				balance = (balance + monthlyContribution) * (1 + r);
			}
			monthlyContribution *= 1.05; // kenaikan gaji 5%
		}
		return Math.round(balance);
	});
</script>

<div class="card p-5">
	<div
		class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4"
	>
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🏛️</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Kalkulator Slip Gaji Bersih & Pensiun BPJS TK (PP 58/2023)
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Simulasi pemotongan resmi PPh 21 TER, iuran BPJS Ketenagakerjaan & Kesehatan, serta
				akumulasi saldo JHT pensiun.
			</p>
		</div>

		<label
			class="flex items-center gap-2 text-xs font-semibold text-[var(--color-ink)] cursor-pointer"
		>
			<input
				type="checkbox"
				bind:checked={includeBpjs}
				class="rounded border-[var(--color-line)]"
			/>
			<span>Potong Iuran BPJS Ketenagakerjaan & Kesehatan</span>
		</label>
	</div>

	<!-- Kontrol Input -->
	<div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
		<CurrencyInput bind:value={grossMonthly} label="Penghasilan Kotor / Bulan" />

		<div>
			<span class="mb-1.5 block text-xs font-semibold text-[var(--color-ink-dim)]">
				Kategori TER (Status PTKP Pajak)
			</span>
			<div
				class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs"
			>
				<button
					class="flex-1 rounded-md py-1.5 font-semibold transition"
					class:bg-[var(--color-accent)]={terCategory === 'A'}
					class:text-white={terCategory === 'A'}
					class:text-[var(--color-ink-dim)]={terCategory !== 'A'}
					onclick={() => (terCategory = 'A')}
				>
					TER A (TK/0, K/0)
				</button>
				<button
					class="flex-1 rounded-md py-1.5 font-semibold transition"
					class:bg-[var(--color-accent)]={terCategory === 'B'}
					class:text-white={terCategory === 'B'}
					class:text-[var(--color-ink-dim)]={terCategory !== 'B'}
					onclick={() => (terCategory = 'B')}
				>
					TER B (K/1, K/2)
				</button>
				<button
					class="flex-1 rounded-md py-1.5 font-semibold transition"
					class:bg-[var(--color-accent)]={terCategory === 'C'}
					class:text-white={terCategory === 'C'}
					class:text-[var(--color-ink-dim)]={terCategory !== 'C'}
					onclick={() => (terCategory = 'C')}
				>
					TER C (K/3)
				</button>
			</div>
		</div>

		<div>
			<label class="block">
				<span class="mb-1.5 block text-xs font-semibold text-[var(--color-ink-dim)]">
					Usia Saat Ini (Untuk Proyeksi JHT 56 Th)
				</span>
				<input class="input num text-xs" type="number" min="18" max="55" bind:value={currentAge} />
			</label>
		</div>
	</div>

	<!-- Rincian Slip Gaji Bersih (Payroll Voucher Grid) -->
	<div class="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
		<!-- Sisi Kiri: Slip Gaji Take-Home Pay -->
		<div
			class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4 space-y-3"
		>
			<div class="flex items-center justify-between border-b border-[var(--color-line)]/50 pb-2">
				<span class="text-xs font-bold uppercase tracking-wider text-[var(--color-ink-dim)]">
					Rincian Slip Gaji Bulanan
				</span>
				<span class="text-[11px] font-semibold text-[var(--color-accent)]">
					PMK 168/2023 & PP 58/2023
				</span>
			</div>

			<div class="flex justify-between text-xs">
				<span class="text-[var(--color-ink-dim)]">Gaji Kotor Bulanan (Gross):</span>
				<strong class="text-[var(--color-ink)]">{rupiah(grossMonthly)}</strong>
			</div>

			<div class="space-y-1.5 border-t border-dashed border-[var(--color-line)] pt-2 text-xs">
				<div class="flex justify-between text-[var(--color-ink-dim)]">
					<span>PPh 21 TER (Tarif {percent(terRate, 2)}):</span>
					<span class="text-rose-400 font-semibold">-{rupiah(pph21)}</span>
				</div>
				{#if includeBpjs}
					<div class="flex justify-between text-[var(--color-ink-dim)]">
						<span>BPJS Ketenagakerjaan (JHT 2% Pekerja):</span>
						<span class="text-rose-400 font-semibold">-{rupiah(jhtWorker)}</span>
					</div>
					<div class="flex justify-between text-[var(--color-ink-dim)]">
						<span>BPJS Ketenagakerjaan (JP 1% Pekerja):</span>
						<span class="text-rose-400 font-semibold">-{rupiah(jpWorker)}</span>
					</div>
					<div class="flex justify-between text-[var(--color-ink-dim)]">
						<span>BPJS Kesehatan (1% Pekerja):</span>
						<span class="text-rose-400 font-semibold">-{rupiah(kesWorker)}</span>
					</div>
				{/if}
			</div>

			<div
				class="flex justify-between border-t border-[var(--color-line)] pt-2 text-xs font-semibold"
			>
				<span class="text-[var(--color-ink-dim)]">Total Potongan Wajib:</span>
				<span class="text-rose-400">-{rupiah(totalDeductions)}</span>
			</div>

			<div
				class="mt-2 rounded-lg bg-[var(--color-void-1)] p-3 border border-[var(--color-line)]/80 flex items-center justify-between"
			>
				<div>
					<span class="text-[11px] uppercase tracking-wide text-[var(--color-ink-dim)] block">
						Gaji Bersih Diterima (Take-Home Pay)
					</span>
					<span class="text-xs text-[var(--color-ink-dim)]">
						Uang riil yang masuk ke rekening tiap bulan
					</span>
				</div>
				<span class="text-xl font-black text-emerald-400">{rupiah(netTakeHomePay)}</span>
			</div>
		</div>

		<!-- Sisi Kanan: Hidden Wealth BPJS Ketenagakerjaan -->
		<div
			class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4 flex flex-col justify-between"
		>
			<div>
				<div class="flex items-center justify-between border-b border-[var(--color-line)]/50 pb-2">
					<span class="text-xs font-bold uppercase tracking-wider text-[var(--color-ink-dim)]">
						Dana Pensiun Tersembunyi (JHT BPJS TK)
					</span>
					<span class="text-xs">🛡️</span>
				</div>

				<div class="mt-3 space-y-2 text-xs">
					<div class="flex justify-between text-[var(--color-ink-dim)]">
						<span>Iuran JHT dari Pekerja (2%):</span>
						<span class="text-[var(--color-ink)] font-semibold">{rupiah(jhtWorker)}/bln</span>
					</div>
					<div class="flex justify-between text-[var(--color-ink-dim)]">
						<span>Iuran JHT dari Pemberi Kerja (3,7%):</span>
						<span class="text-emerald-400 font-semibold">+{rupiah(jhtEmployer)}/bln</span>
					</div>
					<div
						class="flex justify-between text-[var(--color-ink-dim)] border-t border-dashed border-[var(--color-line)] pt-1.5"
					>
						<span>Total Tabungan JHT Masuk Rekening BPJS:</span>
						<strong class="text-[var(--color-accent)]">{rupiah(totalJhtMonthly)}/bulan</strong>
					</div>
				</div>

				<div
					class="mt-4 rounded-xl border border-[var(--color-accent)]/30 bg-sky-500/10 p-3.5 text-center"
				>
					<span class="text-[11px] uppercase tracking-wider text-[var(--color-ink-dim)] block">
						Proyeksi Saldo Klaim JHT Usia Pensiun 56 Tahun ({yearsToPension} Tahun Lagi)
					</span>
					<div class="mt-1 text-2xl font-black text-[var(--color-accent)]">
						{rupiahBrief(projectedJhtLumpSum)}
					</div>
					<span class="mt-1 block text-[11px] text-[var(--color-ink-dim)]">
						(Asumsi imbal hasil pengembangan historis BPJS TK 5,6%/tahun & kenaikan upah 5%/thn)
					</span>
				</div>
			</div>

			<p class="mt-3 text-[11px] text-[var(--color-ink-dim)] leading-relaxed">
				💡 <strong>Insight Cerdas:</strong> Gaji bersih Anda {rupiahBrief(netTakeHomePay)}, namun
				Anda memiliki aset pensiun likuid di BPJS Ketenagakerjaan yang bertambah {rupiah(
					totalJhtMonthly
				)} tiap bulan tanpa membebani arus kas pribadi.
			</p>
		</div>
	</div>
</div>
