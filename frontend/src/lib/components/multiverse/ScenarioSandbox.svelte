<script lang="ts">
	import { rupiahBrief } from '$lib/utils/format';

	let { baseExpense = 5_000_000, baseIncome = 0 }: { baseExpense?: number; baseIncome?: number } =
		$props();

	let extraIncome = $state(0);
	let expenseCutPct = $state(0);
	let extraSavings = $state(0);

	const INCOME_OPTIONS = [
		{ label: 'Normal', value: 0 },
		{ label: '+Rp 1 Jt/bln', value: 1_000_000 },
		{ label: '+Rp 2,5 Jt/bln', value: 2_500_000 },
		{ label: '+Rp 5 Jt/bln', value: 5_000_000 }
	];

	const EXPENSE_OPTIONS = [
		{ label: 'Normal', value: 0 },
		{ label: 'Hemat 10%', value: 0.1 },
		{ label: 'Hemat 20%', value: 0.2 }
	];

	const SAVINGS_OPTIONS = [
		{ label: 'Normal', value: 0 },
		{ label: '+Rp 5 Jt', value: 5_000_000 },
		{ label: '+Rp 15 Jt', value: 15_000_000 },
		{ label: '+Rp 30 Jt', value: 30_000_000 }
	];

	// Estimasi dampak majemuk tahun ke-10 (asumsi return moderat riil ~4%/tahun).
	// Basis penghematan memakai pengeluaran bulanan pengguna, bukan angka tetap.
	let projectedGainY10 = $derived.by(() => {
		const monthlySurplus = extraIncome + expenseCutPct * Math.max(baseExpense, 0);
		const r = 0.04 / 12; // return riil bulanan
		const n = 120; // 10 tahun (120 bulan)

		// Future value of lump sum savings
		const fvSavings = extraSavings * Math.pow(1 + r, n);

		// Future value of monthly contributions
		const fvMonthly = monthlySurplus > 0 ? monthlySurplus * ((Math.pow(1 + r, n) - 1) / r) : 0;

		return Math.round(fvSavings + fvMonthly);
	});

	// Nominal hemat per bulan agar pengguna paham angka absolutnya.
	let monthlySavingAmount = $derived.by(
		() => extraIncome + Math.round(expenseCutPct * Math.max(baseExpense, 0))
	);
</script>

<div class="card p-4">
	<div class="mb-4">
		<h3 class="flex items-center gap-2 text-sm font-semibold text-[var(--color-ink)]">
			<span>🧪</span> Sandbox Simulasi Cepat: "Bagaimana Jika...?"
		</h3>
		<p class="text-xs text-[var(--color-ink-dim)]">
			Uji dampak percepatan finansial jika kamu menambah penghasilan atau menyisihkan bonus hari ini
			{#if baseIncome > 0}
				<span class="text-[var(--color-ink-faint)]"
					>· penghasilan saat ini {rupiahBrief(baseIncome)}/bln</span
				>
			{/if}
		</p>
	</div>

	<div class="space-y-4 text-xs">
		<!-- Pilihan Gaji Tambahan -->
		<div>
			<span class="mb-1.5 block font-semibold text-[var(--color-ink-dim)]"
				>💼 Tambahan Penghasilan Bulanan (Side Hustle / Lembur):</span
			>
			<div class="flex flex-wrap gap-1.5">
				{#each INCOME_OPTIONS as opt}
					<button
						class="chip text-xs"
						class:active={extraIncome === opt.value}
						onclick={() => (extraIncome = opt.value)}
					>
						{opt.label}
					</button>
				{/each}
			</div>
		</div>

		<!-- Pilihan Suntikan Tabungan Awal -->
		<div>
			<span class="mb-1.5 block font-semibold text-[var(--color-ink-dim)]"
				>🎁 Suntikan Modal Awal / THR / Bonus:</span
			>
			<div class="flex flex-wrap gap-1.5">
				{#each SAVINGS_OPTIONS as opt}
					<button
						class="chip text-xs"
						class:active={extraSavings === opt.value}
						onclick={() => (extraSavings = opt.value)}
					>
						{opt.label}
					</button>
				{/each}
			</div>
		</div>

		<!-- Pilihan Penghematan Pengeluaran -->
		<div>
			<span class="mb-1.5 block font-semibold text-[var(--color-ink-dim)]"
				>✂️ Penghematan Pengeluaran Bulanan (Gaya Hidup):</span
			>
			<div class="flex flex-wrap gap-1.5">
				{#each EXPENSE_OPTIONS as opt}
					<button
						class="chip text-xs"
						class:active={expenseCutPct === opt.value}
						onclick={() => (expenseCutPct = opt.value)}
					>
						{opt.label}
					</button>
				{/each}
			</div>
			<p class="mt-1 text-[11px] text-[var(--color-ink-faint)]">
				Basis pengeluaranmu: {rupiahBrief(baseExpense)}/bln · hemat {rupiahBrief(
					Math.round(expenseCutPct * Math.max(baseExpense, 0))
				)}/bln
			</p>
		</div>

		<!-- Hasil Proyeksi Nilai Tambah -->
		{#if extraIncome > 0 || extraSavings > 0 || expenseCutPct > 0}
			<div
				class="rounded-xl border border-emerald-500/50 bg-emerald-500/10 p-3.5 text-left transition-all"
			>
				<div class="flex items-center justify-between gap-3">
					<span class="font-bold text-xs text-emerald-400"
						>✨ Potensi Tambahan Kekayaan Riil (Tahun ke-10):</span
					>
					<span class="num text-base font-extrabold text-emerald-300">
						+{rupiahBrief(projectedGainY10)}
					</span>
				</div>
				<p class="mt-1 text-[11px] leading-relaxed text-[var(--color-ink-dim)]">
					Surplus bulanan total <strong class="text-emerald-300"
						>{rupiahBrief(monthlySavingAmount)}/bln</strong
					> bila disalurkan ke instrumen investasi majemuk riil (~4%/thn) dapat mempercepat capaian target
					100 Juta dan 1 Miliar Pertama hingga 2–4 tahun lebih awal.
				</p>
			</div>
		{/if}
	</div>
</div>
