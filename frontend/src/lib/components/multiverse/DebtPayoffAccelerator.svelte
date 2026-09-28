<script lang="ts">
	import type { Profile, Twin } from '$lib/api/types';
	import { rupiah, rupiahBrief, percent } from '$lib/utils/format';

	let { profile, twins = [] }: { profile?: Profile; twins?: Twin[] } = $props();

	type Strategy = 'avalanche' | 'snowball';
	let strategy = $state<Strategy>('avalanche');

	let extraPaymentMonthly = $state<number>(500_000); // Tambahan dana per bulan

	interface DebtItem {
		id: string;
		name: string;
		principal: number;
		monthlyPayment: number;
		annualRate: number; // e.g. 0.12 = 12%
		tenorMonths: number;
		icon: string;
	}

	// Kumpulkan seluruh utang aktif dari profil atau twin
	let debts = $derived.by<DebtItem[]>(() => {
		const list: DebtItem[] = [];

		// Utang berjalan dari profil pengguna
		if (profile?.existing_debt && profile.existing_debt.principal > 0) {
			list.push({
				id: 'existing',
				name: 'Utang Berjalan Saat Ini',
				principal: profile.existing_debt.principal,
				monthlyPayment:
					profile.existing_debt.monthly_payment || profile.existing_debt.principal / 12,
				annualRate: profile.existing_debt.annual_rate || 0.12,
				tenorMonths: profile.existing_debt.tenor_months || 12,
				icon: '💳'
			});
		}

		// Cari pinjaman dari twin keputusan jika ada
		for (const t of twins) {
			const meta = t.config?.meta as Record<string, unknown> | undefined;
			if (meta?.kind && typeof meta?.amount === 'number' && Number(meta.amount) > 0) {
				const id = `twin-${t.code}-${meta.kind}`;
				if (!list.some((d) => d.id === id)) {
					const rateDaily = typeof meta.rate_daily === 'number' ? meta.rate_daily : 0.003;
					list.push({
						id,
						name: `${t.label} (${String(meta.kind).toUpperCase()})`,
						principal: Number(meta.amount),
						monthlyPayment: Number(meta.amount) / Number(meta.tenor || 6),
						annualRate: rateDaily * 365,
						tenorMonths: Number(meta.tenor || 12),
						icon: '⚡'
					});
				}
			}
		}

		// Jika pengguna tidak punya utang sama sekali, sediakan contoh edukatif realistis
		if (list.length === 0) {
			list.push(
				{
					id: 'demo-pinjol',
					name: 'Pinjol Konsumtif (Bunga OJK 0,3%/hari)',
					principal: 3_000_000,
					monthlyPayment: 1_200_000,
					annualRate: 0.003 * 365, // ~109,5%/thn
					tenorMonths: 3,
					icon: '📱'
				},
				{
					id: 'demo-paylater',
					name: 'Paylater E-Commerce',
					principal: 4_500_000,
					monthlyPayment: 850_000,
					annualRate: 0.28, // 28%/thn
					tenorMonths: 6,
					icon: '🛍️'
				},
				{
					id: 'demo-motor',
					name: 'Cicilan Kendaraan Leasing',
					principal: 15_000_000,
					monthlyPayment: 850_000,
					annualRate: 0.14, // 14%/thn
					tenorMonths: 24,
					icon: '🛵'
				}
			);
		}

		return list;
	});

	// Urutan pembayaran sesuai strategi
	let sortedDebts = $derived.by(() => {
		const copy = [...debts];
		if (strategy === 'snowball') {
			// Snowball: pokok terkecil dahulu
			return copy.sort((a, b) => a.principal - b.principal);
		}
		// Avalanche: bunga tertinggi dahulu
		return copy.sort((a, b) => b.annualRate - a.annualRate);
	});

	// Simulasi pembayaran utang bulanan
	interface PayoffSummary {
		monthsToPayoff: number;
		totalInterestPaid: number;
		interestSavedVsNormal: number;
		monthsSaved: number;
	}

	function simulatePayoff(extraMonthly: number, strat: Strategy): PayoffSummary {
		let currentDebts = debts.map((d) => ({
			balance: d.principal,
			minPayment: d.monthlyPayment,
			monthlyRate: d.annualRate / 12,
			principal: d.principal,
			annualRate: d.annualRate
		}));

		// Urutkan
		if (strat === 'snowball') {
			currentDebts.sort((a, b) => a.principal - b.principal);
		} else {
			currentDebts.sort((a, b) => b.annualRate - a.annualRate);
		}

		let month = 0;
		let totalInterest = 0;
		const maxMonths = 360;

		while (currentDebts.some((d) => d.balance > 100) && month < maxMonths) {
			month++;
			let surplusExtra = extraMonthly;

			for (const d of currentDebts) {
				if (d.balance <= 0) continue;
				const interestMonth = d.balance * d.monthlyRate;
				totalInterest += interestMonth;
				d.balance += interestMonth;

				// Pembayaran minimum
				const pay = Math.min(d.balance, d.minPayment);
				d.balance -= pay;
			}

			// Alokasikan dana ekstra ke target utang prioritas
			for (const d of currentDebts) {
				if (d.balance > 0 && surplusExtra > 0) {
					const payExtra = Math.min(d.balance, surplusExtra);
					d.balance -= payExtra;
					surplusExtra -= payExtra;
				}
			}
		}

		// Hitung pembanding tanpa ekstra (normal)
		let normalDebts = debts.map((d) => ({
			balance: d.principal,
			minPayment: d.monthlyPayment,
			monthlyRate: d.annualRate / 12
		}));
		let normalMonth = 0;
		let normalInterest = 0;

		while (normalDebts.some((d) => d.balance > 100) && normalMonth < maxMonths) {
			normalMonth++;
			for (const d of normalDebts) {
				if (d.balance <= 0) continue;
				const interestMonth = d.balance * d.monthlyRate;
				normalInterest += interestMonth;
				d.balance += interestMonth;
				const pay = Math.min(d.balance, d.minPayment);
				d.balance -= pay;
			}
		}

		return {
			monthsToPayoff: month,
			totalInterestPaid: Math.round(totalInterest),
			interestSavedVsNormal: Math.max(0, Math.round(normalInterest - totalInterest)),
			monthsSaved: Math.max(0, normalMonth - month)
		};
	}

	let acceleratedPlan = $derived(simulatePayoff(extraPaymentMonthly, strategy));
	let baselinePlan = $derived(simulatePayoff(0, strategy));

	let totalInitialDebt = $derived(debts.reduce((sum, d) => sum + d.principal, 0));
	let totalMinMonthly = $derived(debts.reduce((sum, d) => sum + d.monthlyPayment, 0));
</script>

<div class="card p-5">
	<!-- Header -->
	<div
		class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4"
	>
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🚀</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Akselerator Bebas Utang (Debt Freedom Runway)
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Simulasi percepatan pelunasan utang (Pinjol, Paylater, KTA, Leasing) dengan metode matematis
				Debt Avalanche vs psikologis Debt Snowball.
			</p>
		</div>

		<!-- Strategy Toggle -->
		<div
			class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs"
		>
			<button
				class="rounded-md px-3 py-1 font-semibold transition {strategy === 'avalanche'
					? 'bg-[var(--color-accent)] text-white'
					: 'text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]'}"
				onclick={() => (strategy = 'avalanche')}
			>
				🔥 Longsoran Bunga (Avalanche)
			</button>
			<button
				class="rounded-md px-3 py-1 font-semibold transition {strategy === 'snowball'
					? 'bg-[var(--color-accent)] text-white'
					: 'text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]'}"
				onclick={() => (strategy = 'snowball')}
			>
				⛄ Bola Salju (Snowball)
			</button>
		</div>
	</div>

	<!-- Penjelasan Strategi -->
	<div
		class="mt-3.5 rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] p-3 text-xs text-[var(--color-ink-dim)]"
	>
		{#if strategy === 'avalanche'}
			<strong class="text-amber-400">Metode Debt Avalanche (Rekomendasi Matematis):</strong>
			Memprioritaskan pelunasan utang dengan <strong>suku bunga tertinggi terlebih dahulu</strong> (seperti
			bunga pinjol 0,3%/hari atau paylater). Strategi ini meminimalkan total nominal bunga yang harus
			kamu bayar ke lembaga keuangan.
		{:else}
			<strong class="text-cyan-400">Metode Debt Snowball (Rekomendasi Psikologis):</strong>
			Memprioritaskan pelunasan utang dengan <strong>saldo pokok terkecil terlebih dahulu</strong> tanpa
			melihat bunga. Kemenangan cepat saat satu utang lunas memberikan dorongan mental dan motivasi tinggi
			untuk menuntaskan utang berikutnya.
		{/if}
	</div>

	<!-- Kartu Ringkasan Dampak Akselerasi -->
	<div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<span class="text-[11px] text-[var(--color-ink-dim)]">Total Pokok Utang</span>
			<div class="mt-1 text-lg font-black text-rose-400">{rupiah(totalInitialDebt)}</div>
			<span class="text-[10px] text-[var(--color-ink-dim)]">{debts.length} pos kewajiban</span>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<span class="text-[11px] text-[var(--color-ink-dim)]">Target Bebas Utang</span>
			<div class="mt-1 text-lg font-black text-emerald-400">
				{acceleratedPlan.monthsToPayoff} Bulan
			</div>
			<span class="text-[10px] text-emerald-400 font-semibold">
				{acceleratedPlan.monthsSaved > 0
					? `+${acceleratedPlan.monthsSaved} bulan lebih cepat (vs ${baselinePlan.monthsToPayoff} bln)`
					: `Selesai dalam ${baselinePlan.monthsToPayoff} bulan`}
			</span>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<span class="text-[11px] text-[var(--color-ink-dim)]">Total Bunga Dihemat</span>
			<div class="mt-1 text-lg font-black text-cyan-400">
				{rupiah(acceleratedPlan.interestSavedVsNormal)}
			</div>
			<span class="text-[10px] text-[var(--color-ink-dim)]">Efisiensi pembayaran bunga</span>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3">
			<span class="text-[11px] text-[var(--color-ink-dim)]">Cicilan Minimum/Bulan</span>
			<div class="mt-1 text-lg font-black text-[var(--color-ink)]">
				{rupiahBrief(totalMinMonthly)}
			</div>
			<span class="text-[10px] text-[var(--color-ink-dim)]">Di luar tambahan ekstra</span>
		</div>
	</div>

	<!-- Kontrol Slider Tambahan Pembayaran Ekstra -->
	<div class="mt-4 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-4">
		<div class="flex flex-wrap items-center justify-between gap-2">
			<div>
				<span class="text-xs font-bold text-[var(--color-ink)]"
					>Tambahan Anggaran Pelunasan Utang per Bulan:</span
				>
				<p class="text-[11px] text-[var(--color-ink-dim)]">
					Disisihkan dari pemotongan pengeluaran gaya hidup, bonus kerja, atau hasil kerja
					sampingan.
				</p>
			</div>
			<div class="text-right">
				<span class="text-base font-extrabold text-[var(--color-accent)]"
					>+{rupiah(extraPaymentMonthly)}</span
				>
				<span class="text-xs text-[var(--color-ink-dim)]">/bulan</span>
			</div>
		</div>

		<div class="mt-3 flex items-center gap-4">
			<input
				type="range"
				min="0"
				max="5000000"
				step="100000"
				class="w-full accent-[var(--color-accent)]"
				bind:value={extraPaymentMonthly}
			/>
		</div>

		<div class="mt-2 flex justify-between text-[10px] text-[var(--color-ink-dim)]">
			<span>Rp 0 (Hanya Minimum)</span>
			<span>+Rp 1.000.000</span>
			<span>+Rp 2.500.000</span>
			<span>+Rp 5.000.000</span>
		</div>
	</div>

	<!-- Tabel Urutan Pelunasan Utang -->
	<div class="mt-4 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4">
		<div class="flex items-center justify-between">
			<span class="text-xs font-bold text-[var(--color-ink)]">
				Urutan Prioritas Pelunasan ({strategy === 'avalanche'
					? 'Bunga Tertinggi'
					: 'Saldo Terkecil'}):
			</span>
			<span class="text-[11px] text-[var(--color-ink-dim)]">
				Fokuskan seluruh dana ekstra pada <strong>Utang #1</strong> hingga lunas!
			</span>
		</div>

		<div class="mt-3 overflow-x-auto">
			<table class="w-full text-left text-xs">
				<thead>
					<tr class="border-b border-[var(--color-line)] text-[11px] text-[var(--color-ink-dim)]">
						<th scope="col" class="pb-2 font-semibold">Prioritas</th>
						<th scope="col" class="pb-2 font-semibold">Nama Kewajiban</th>
						<th scope="col" class="pb-2 font-semibold text-right">Sisa Pokok</th>
						<th scope="col" class="pb-2 font-semibold text-right">Bunga/Tahun</th>
						<th scope="col" class="pb-2 font-semibold text-right">Cicilan Normal</th>
						<th scope="col" class="pb-2 font-semibold text-center">Fokus Ekstra</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-[var(--color-line)]/50">
					{#each sortedDebts as debt, idx (debt.id)}
						<tr class="hover:bg-[var(--color-void-1)] transition">
							<td class="py-2.5 font-bold text-center">
								<span
									class="inline-block h-5 w-5 rounded-full text-center leading-5 font-mono text-[11px] {idx ===
									0
										? 'bg-rose-500/20 text-rose-400 font-extrabold'
										: 'bg-[var(--color-void-3)] text-[var(--color-ink-dim)]'}"
								>
									{idx + 1}
								</span>
							</td>
							<td class="py-2.5 font-semibold text-[var(--color-ink)]">
								<div class="flex items-center gap-1.5">
									<span>{debt.icon}</span>
									<span>{debt.name}</span>
								</div>
							</td>
							<td class="py-2.5 text-right font-mono font-bold text-[var(--color-ink)]">
								{rupiah(debt.principal)}
							</td>
							<td class="py-2.5 text-right font-mono font-semibold text-amber-400">
								{percent(debt.annualRate, 1)}
							</td>
							<td class="py-2.5 text-right font-mono text-[var(--color-ink-dim)]">
								{rupiahBrief(debt.monthlyPayment)}/bln
							</td>
							<td class="py-2.5 text-center">
								{#if idx === 0 && extraPaymentMonthly > 0}
									<span
										class="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400"
									>
										🎯 Target Ekstra (+{rupiahBrief(extraPaymentMonthly)})
									</span>
								{:else}
									<span class="text-[10px] text-[var(--color-ink-dim)]">Bayar minimum</span>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>

	<!-- 3 Langkah Bebas Utang -->
	<div
		class="mt-4 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-4 text-xs"
	>
		<span class="font-bold text-[var(--color-ink)]"
			>🛡️ Golden Rules Melunasi Utang di Indonesia:</span
		>
		<div
			class="mt-2.5 grid grid-cols-1 gap-2.5 sm:grid-cols-3 text-[11px] text-[var(--color-ink-dim)]"
		>
			<div>
				<strong class="text-cyan-400">1. Stop Utang Baru:</strong> Hentikan menambah saldo paylater dan
				kartu kredit saat sedang menjalankan program percepatan bebas utang.
			</div>
			<div>
				<strong class="text-amber-400">2. Amankan Dana Darurat Mini:</strong> Simpan minimal Rp1–2 juta
				di kas likuid agar saat ban motor bocor atau sakit ringan, kamu tidak perlu pinjol darurat baru.
			</div>
			<div>
				<strong class="text-emerald-400">3. Roll-Over Cicilan:</strong> Saat utang #1 lunas, alihkan seluruh
				anggarannya ke utang #2 untuk efek bola salju yang eksponensial!
			</div>
		</div>
	</div>
</div>
