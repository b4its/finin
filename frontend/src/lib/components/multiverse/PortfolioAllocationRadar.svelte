<script lang="ts">
	import type { Twin } from '$lib/api/types';
	import { rupiahBrief, percent } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let { twins }: { twins: Twin[] } = $props();

	let year = $state(10);

	let allocations = $derived(
		twins.map((t) => {
			const pt = t.yearly_series.find((p) => p.year === year) ?? t.yearly_series[t.yearly_series.length - 1];
			const cash = Math.max(0, pt?.cash ?? 0);
			const invest = Math.max(0, pt?.invest ?? 0);

			// Hitung nilai properti dan kendaraan jika ada di config
			const cfg = t.config ?? {};
			const propInit = (cfg.property_initial_value as number) || 0;
			const propApprec = (cfg.property_appreciation_annual as number) || 0;
			const propVal = propInit > 0 ? propInit * Math.pow(1 + propApprec / 12, year * 12) : 0;

			const vehInit = (cfg.vehicle_initial_value as number) || 0;
			const vehDeprec = (cfg.vehicle_depreciation_annual as number) || 0;
			const vehVal = vehInit > 0 ? vehInit * Math.max(0.05, Math.pow(1 - vehDeprec / 12, year * 12)) : 0;

			const realAssets = propVal + vehVal;
			const totalAssets = Math.max(1, cash + invest + realAssets);

			const pCash = cash / totalAssets;
			const pInvest = invest / totalAssets;
			const pReal = realAssets / totalAssets;

			// Herfindahl-Hirschman Index untuk diversifikasi aset
			const hhi = pCash * pCash + pInvest * pInvest + pReal * pReal;
			// Normalisasi skor diversifikasi (0..100)
			const divScore = Math.round(Math.max(10, Math.min(100, (1 - (hhi - 0.33) / 0.67) * 100)));

			let statusLabel = 'Diversifikasi Seimbang';
			let statusColor = 'text-emerald-400 bg-emerald-500/10';
			let recommendation = 'Komposisi aset terjaga dengan baik.';

			if (divScore < 45) {
				statusLabel = 'Konsentrasi Sangat Tinggi';
				statusColor = 'text-rose-400 bg-rose-500/10';
				if (pReal > 0.6) {
					recommendation = 'Kekayaan terkunci di aset fisik (properti/kendaraan). Perkuat tabungan likuid dan instrumen pasar modal.';
				} else if (pCash > 0.6) {
					recommendation = 'Terlalu banyak kas menganggur, rentan tergerus inflasi. Alihkan porsi surplus ke obligasi SBN atau reksadana.';
				} else {
					recommendation = 'Portofolio terkonsentrasi pada satu instrumen berisiko. Imbangi dengan aset berpendapatan tetap.';
				}
			} else if (divScore < 70) {
				statusLabel = 'Diversifikasi Moderat';
				statusColor = 'text-amber-400 bg-amber-500/10';
				recommendation = 'Cukup baik, pertimbangkan rebalancing berkala tiap 1–2 tahun untuk mengunci imbal hasil.';
			}

			return {
				code: t.code,
				label: t.label,
				color: t.color,
				icon: t.icon,
				cash,
				invest,
				realAssets,
				totalAssets,
				pCash,
				pInvest,
				pReal,
				divScore,
				statusLabel,
				statusColor,
				recommendation
			};
		})
	);
</script>

<div class="card p-5">
	<div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4">
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🧭</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Radar Alokasi Aset & Skor Diversifikasi Portofolio
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Menganalisis keseimbangan likuiditas kas, portofolio pasar modal, dan aset riil untuk menghindari <em>single-asset concentration risk</em>.
			</p>
		</div>

		<div class="flex items-center gap-2">
			<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Tahun Evaluasi:</span>
			<div class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs">
				{#each [5, 10, 20] as y}
					<button
						class="rounded-md px-2.5 py-1 font-semibold transition"
						class:bg-[var(--color-accent)]={year === y}
						class:text-white={year === y}
						class:text-[var(--color-ink-dim)]={year !== y}
						onclick={() => (year = y)}
					>
						Th-{y}
					</button>
				{/each}
			</div>
		</div>
	</div>

	<!-- Legend Alokasi -->
	<div class="mt-4 flex flex-wrap items-center gap-4 text-xs text-[var(--color-ink-dim)]">
		<span class="flex items-center gap-1.5">
			<span class="inline-block h-3 w-3 rounded-sm bg-sky-400"></span>
			Kas & Likuiditas
		</span>
		<span class="flex items-center gap-1.5">
			<span class="inline-block h-3 w-3 rounded-sm bg-indigo-500"></span>
			Investasi (SBN/Saham/Pasar Uang)
		</span>
		<span class="flex items-center gap-1.5">
			<span class="inline-block h-3 w-3 rounded-sm bg-emerald-500"></span>
			Aset Riil (Properti / Kendaraan)
		</span>
	</div>

	<!-- Grid Alokasi Per Twin -->
	<div class="mt-4 space-y-3.5">
		{#each allocations as item (item.code)}
			<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3.5">
				<div class="flex flex-wrap items-center justify-between gap-2">
					<div class="flex items-center gap-2">
						<span class="text-sm">{twinIcon(item.icon)}</span>
						<span class="text-xs font-bold text-[var(--color-ink)]">
							Twin {item.code}: {item.label}
						</span>
						<span class="text-xs text-[var(--color-ink-dim)]">
							· Total Aset: <strong class="text-[var(--color-ink)]">{rupiahBrief(item.totalAssets)}</strong>
						</span>
					</div>

					<div class="flex items-center gap-2">
						<span class="text-[11px] font-semibold text-[var(--color-ink-dim)]">Skor Diversifikasi:</span>
						<span class="rounded-full px-2 py-0.5 text-[11px] font-bold {item.statusColor}">
							{item.divScore}/100 ({item.statusLabel})
						</span>
					</div>
				</div>

				<!-- Bar Komposisi Bertumpuk -->
				<div class="mt-3 flex h-3.5 w-full overflow-hidden rounded-full bg-[var(--color-void-3)]">
					{#if item.pCash > 0}
						<div
							style="width: {item.pCash * 100}%;"
							class="bg-sky-400 transition-all duration-300"
							title="Kas: {percent(item.pCash, 1)}"
						></div>
					{/if}
					{#if item.pInvest > 0}
						<div
							style="width: {item.pInvest * 100}%;"
							class="bg-indigo-500 transition-all duration-300"
							title="Investasi: {percent(item.pInvest, 1)}"
						></div>
					{/if}
					{#if item.pReal > 0}
						<div
							style="width: {item.pReal * 100}%;"
							class="bg-emerald-500 transition-all duration-300"
							title="Aset Riil: {percent(item.pReal, 1)}"
						></div>
					{/if}
				</div>

				<!-- Angka Proporsi Detail & Rekomendasi -->
				<div class="mt-2.5 flex flex-wrap items-center justify-between gap-2 text-[11px]">
					<div class="flex flex-wrap gap-3 text-[var(--color-ink-dim)]">
						<span>Kas: <strong class="text-sky-400">{percent(item.pCash, 0)}</strong> ({rupiahBrief(item.cash)})</span>
						<span>Investasi: <strong class="text-indigo-400">{percent(item.pInvest, 0)}</strong> ({rupiahBrief(item.invest)})</span>
						{#if item.pReal > 0}
							<span>Aset Riil: <strong class="text-emerald-400">{percent(item.pReal, 0)}</strong> ({rupiahBrief(item.realAssets)})</span>
						{/if}
					</div>

					<p class="text-[11px] text-[var(--color-ink-dim)] italic">
						💡 {item.recommendation}
					</p>
				</div>
			</div>
		{/each}
	</div>
</div>
