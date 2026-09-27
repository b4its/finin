<script lang="ts">
	import type { Twin } from '$lib/api/types';
	import { rupiahBrief, percent, rupiah } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let { twins }: { twins: Twin[] } = $props();

	let horizonYear = $state(10);
	let selectedBasket = $state<'general' | 'education' | 'property' | 'food' | 'health'>('education');

	const BASKETS = {
		general: {
			id: 'general',
			name: 'IHK Umum BI',
			rate: 0.03,
			icon: '📊',
			unit: 'Keranjang Konsumsi',
			basePrice: 500_000,
			source: 'BI / BPS Target 2,5% ± 1%',
			description: 'Daya beli umum berdasarkan Indeks Harga Konsumen nasional.'
		},
		education: {
			id: 'education',
			name: 'Pendidikan Tinggi',
			rate: 0.08,
			icon: '🎓',
			unit: 'Semester Kuliah S1',
			basePrice: 12_500_000,
			source: 'BPS & Survei Biaya UKT PTN/PTS',
			description: 'Inflasi biaya pendidikan tinggi di Indonesia rata-rata 8–10% per tahun.'
		},
		property: {
			id: 'property',
			name: 'Properti & Hunian',
			rate: 0.065,
			icon: '🏠',
			unit: 'm² Hunian Jabodetabek',
			basePrice: 15_000_000,
			source: 'Indeks Harga Properti Residensial BI',
			description: 'Apresiasi dan inflasi harga tanah/rumah tinggal perkotaan.'
		},
		food: {
			id: 'food',
			name: 'Pangan & Sembako',
			rate: 0.045,
			icon: '🍲',
			unit: 'Paket Pangan Keluarga',
			basePrice: 1_500_000,
			source: 'Volatile Foods BPS Nasional',
			description: 'Inflasi harga bahan pokok, protein, beras, dan minyak goreng.'
		},
		health: {
			id: 'health',
			name: 'Kesehatan & Medis',
			rate: 0.10,
			icon: '🏥',
			unit: 'Hari Rawat Inap Medis',
			basePrice: 3_500_000,
			source: 'Mercer Marsh Benefits Medical Trend',
			description: 'Inflasi medis swasta dan biaya obat-obatan modern (~10–12% per tahun).'
		}
	};

	let basket = $derived(BASKETS[selectedBasket]);

	// Hitung harga satuan masa depan pada horizonYear
	let futureUnitPrice = $derived(basket.basePrice * Math.pow(1 + basket.rate, horizonYear));

	// Data terkomputasi per twin
	let twinStats = $derived(
		twins.map((t) => {
			const pt = t.yearly_series.find((p) => p.year === horizonYear) ?? t.yearly_series[t.yearly_series.length - 1];
			const nwNominal = pt?.net_worth ?? 0;
			// Nilai riil diukur terhadap keranjang inflasi ini
			const nwRealBasket = nwNominal / Math.pow(1 + basket.rate, horizonYear);
			const unitsCount = futureUnitPrice > 0 ? Math.max(0, Math.floor(nwNominal / futureUnitPrice)) : 0;
			const erosion = Math.max(0, nwNominal - nwRealBasket);
			const retentionRate = nwNominal > 0 ? nwRealBasket / nwNominal : 0;

			return {
				code: t.code,
				label: t.label,
				color: t.color,
				icon: t.icon,
				nwNominal,
				nwRealBasket,
				unitsCount,
				erosion,
				retentionRate
			};
		})
	);

	// Baseline untuk perbandingan
	let baseline = $derived(twinStats.find((s) => s.code === '0'));
</script>

<div class="card p-5">
	<div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4">
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">⚖️</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Kalkulator Daya Beli Keranjang Inflasi Riil
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Bongkar <em>"Money Illusion"</em>: Mengukur nilai riil uangmu terhadap kebutuhan nyata di Indonesia.
			</p>
		</div>

		<div class="flex flex-wrap items-center gap-2">
			<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Horizon:</span>
			<div class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs">
				{#each [5, 10, 20] as y}
					<button
						class="rounded-md px-2.5 py-1 font-semibold transition"
						class:bg-[var(--color-accent)]={horizonYear === y}
						class:text-white={horizonYear === y}
						class:text-[var(--color-ink-dim)]={horizonYear !== y}
						onclick={() => (horizonYear = y)}
					>
						{y} Thn
					</button>
				{/each}
			</div>
		</div>
	</div>

	<!-- Selector Keranjang Kebutuhan -->
	<div class="mt-4">
		<span class="mb-2 block text-xs font-semibold text-[var(--color-ink-dim)]">
			Pilih Keranjang Inflasi Sektoral:
		</span>
		<div class="grid grid-cols-2 gap-2 sm:grid-cols-5">
			{#each Object.values(BASKETS) as b}
				<button
					class="flex flex-col items-center rounded-xl border p-2.5 text-center transition {selectedBasket === b.id ? 'border-[var(--color-accent)] bg-sky-500/10' : 'border-[var(--color-line)] bg-[var(--color-void-2)]'}"
					onclick={() => (selectedBasket = b.id as any)}
				>
					<span class="text-lg">{b.icon}</span>
					<span class="mt-1 text-xs font-bold text-[var(--color-ink)]">{b.name}</span>
					<span class="text-[10px] text-[var(--color-accent)]">+{percent(b.rate, 1)}/thn</span>
				</button>
			{/each}
		</div>
		<div class="mt-2.5 rounded-lg border border-[var(--color-line)]/50 bg-[var(--color-void-1)] p-2.5 text-xs text-[var(--color-ink-dim)]">
			<span class="font-semibold text-[var(--color-ink)]">{basket.icon} {basket.name}:</span> {basket.description}
			<span class="ml-1 text-[11px] text-[var(--color-ink-dim)]/80">({basket.source})</span>
			<div class="mt-1 text-[11px]">
				Harga 1 {basket.unit} saat ini: <strong class="text-[var(--color-ink)]">{rupiah(basket.basePrice)}</strong>
				→ Proyeksi Th-{horizonYear}: <strong class="text-orange-400">{rupiah(futureUnitPrice)}</strong>
			</div>
		</div>
	</div>

	<!-- Grid Perbandingan Daya Beli Tiap Twin -->
	<div class="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
		{#each twinStats as st (st.code)}
			{@const diffFromBaseline = baseline && st.code !== '0' ? st.unitsCount - baseline.unitsCount : 0}
			<div
				class="relative flex flex-col justify-between rounded-xl border p-3.5 transition"
				style="border-left: 4px solid {st.color};"
				class:bg-[var(--color-void-2)]={st.code !== '0'}
				class:bg-[var(--color-void-3)]={st.code === '0'}
			>
				<div>
					<div class="flex items-center justify-between">
						<span class="flex items-center gap-1.5 text-xs font-bold text-[var(--color-ink)]">
							<span>{twinIcon(st.icon)}</span>
							Twin {st.code}: {st.label}
						</span>
						<span
							class="rounded-full px-2 py-0.5 text-[10px] font-semibold {st.retentionRate >= 0.5 ? 'bg-emerald-500/15 text-emerald-400' : st.retentionRate >= 0.3 ? 'bg-amber-500/15 text-amber-400' : 'bg-rose-500/15 text-rose-400'}"
						>
							Retensi Daya Beli {percent(st.retentionRate, 0)}
						</span>
					</div>

					<!-- Kartu Ekuivalensi Fisik Nyata -->
					<div class="mt-3 rounded-lg border border-[var(--color-line)]/60 bg-[var(--color-void-1)] p-3 text-center">
						<div class="text-[11px] uppercase tracking-wider text-[var(--color-ink-dim)]">
							Daya Beli Ekuivalen Riil
						</div>
						<div class="mt-1 flex items-baseline justify-center gap-1.5">
							<span class="text-2xl font-black text-[var(--color-accent)]">{st.unitsCount.toLocaleString('id-ID')}</span>
							<span class="text-xs font-semibold text-[var(--color-ink)]">{basket.unit}</span>
						</div>
						{#if st.code !== '0' && diffFromBaseline !== 0}
							<div
								class="mt-1 text-[11px] font-semibold"
								class:text-emerald-400={diffFromBaseline > 0}
								class:text-rose-400={diffFromBaseline < 0}
							>
								{diffFromBaseline > 0 ? `+${diffFromBaseline}` : diffFromBaseline} {basket.unit} vs Baseline
							</div>
						{/if}
					</div>

					<!-- Rincian Nominal vs Riil -->
					<div class="mt-3 space-y-1.5 text-xs">
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>Net Worth Nominal:</span>
							<span class="font-semibold text-[var(--color-ink)]">{rupiahBrief(st.nwNominal)}</span>
						</div>
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>Daya Beli Hari Ini (Riil):</span>
							<span class="font-bold text-emerald-400">{rupiahBrief(st.nwRealBasket)}</span>
						</div>
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>Tergerus Inflasi ({percent(basket.rate, 1)}/thn):</span>
							<span class="font-semibold text-rose-400">-{rupiahBrief(st.erosion)}</span>
						</div>
					</div>
				</div>

				<div class="mt-3 border-t border-[var(--color-line)]/40 pt-2 text-[11px]">
					{#if st.retentionRate >= 0.55}
						<span class="text-emerald-400">🛡️ Portofolio mengalahkan inflasi sektor ini secara optimal.</span>
					{:else if st.retentionRate >= 0.35}
						<span class="text-amber-400">⚠️ Daya beli terjaga moderat, imbangi instrumen dengan imbal hasil riil.</span>
					{:else}
						<span class="text-rose-400">🚨 Risiko erosi daya beli parah akibat inflasi majemuk.</span>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>
