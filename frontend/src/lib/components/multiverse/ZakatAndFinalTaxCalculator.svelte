<script lang="ts">
	import type { Twin } from '$lib/api/types';
	import { rupiah, rupiahBrief, percent } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let { twins }: { twins: Twin[] } = $props();

	let year = $state(10);
	let goldPricePerGram = $state(1_450_000); // Acuan emas Antam 2026

	// Nisab Zakat Mal: 85 gram emas
	let nisabAmount = $derived(85 * goldPricePerGram);

	let zakatStats = $derived(
		twins.map((t) => {
			const pt = t.yearly_series.find((p) => p.year === year) ?? t.yearly_series[t.yearly_series.length - 1];
			const nw = pt?.net_worth ?? 0;
			const isNisabReached = nw >= nisabAmount;
			const zakatAnnual = isNisabReached ? nw * 0.025 : 0;
			const zakatMonthly = zakatAnnual / 12;

			// Hitung Tax Alpha penghematan PPh Final vs Deposito 20%
			// Twin yang menaruh di Reksa Dana (0% PPh) atau SBN (10% PPh) menghemat pajak
			const cfg = t.config ?? {};
			const inst = (cfg.instrument as string) || 'money_market';
			let taxRate = 0.20; // baseline deposito 20%
			if (inst === 'bond') taxRate = 0.10; // SBN ritel 10%
			if (inst === 'money_market' || inst === 'stock') taxRate = 0.00; // Reksa dana 0% (bukan objek pajak)

			const taxSavingsRate = 0.20 - taxRate;
			// Estimasi imbal hasil tahunan ~5%
			const annualGain = nw * 0.05;
			const annualTaxSaved = annualGain * taxSavingsRate;
			const cumulativeTaxSaved = annualTaxSaved * year;

			return {
				code: t.code,
				label: t.label,
				color: t.color,
				icon: t.icon,
				nw,
				isNisabReached,
				zakatAnnual,
				zakatMonthly,
				inst,
				taxRate,
				taxSavingsRate,
				annualTaxSaved,
				cumulativeTaxSaved
			};
		})
	);
</script>

<div class="card p-5">
	<div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4">
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🌙</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Kalkulator Zakat Mal & Efisiensi Pajak Final (PPh Pasal 4(2))
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Melacak kewajiban Zakat Mal (nisab 85 gr emas) dan penghematan pajak investasi (*Tax Alpha*) berdasarkan regulasi perpajakan RI.
			</p>
		</div>

		<div class="flex flex-wrap items-center gap-3">
			<div class="flex items-center gap-2">
				<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Tahun:</span>
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
	</div>

	<!-- Info Bar Nisab Emas & Pajak Final -->
	<div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
			<div class="flex items-center justify-between text-xs">
				<span class="font-bold text-[var(--color-ink)]">Ambang Nisab Zakat Mal (85 gr Emas)</span>
				<span class="rounded-full bg-amber-500/10 px-2 py-0.5 font-bold text-amber-400">
					{rupiah(nisabAmount)}
				</span>
			</div>
			<p class="mt-1 text-[11px] text-[var(--color-ink-dim)]">
				Berdasarkan ketentuan BAZNAS (85 gr emas × acuan Antam Rp{goldPricePerGram.toLocaleString('id-ID')}/gr). Wajib ditunaikan 2,5% per tahun bila mencapai haul & nisab.
			</p>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
			<div class="flex items-center justify-between text-xs">
				<span class="font-bold text-[var(--color-ink)]">Tax Alpha Investasi Indonesia</span>
				<span class="rounded-full bg-emerald-500/10 px-2 py-0.5 font-bold text-emerald-400">
					Hemat 10%–20% PPh
				</span>
			</div>
			<p class="mt-1 text-[11px] text-[var(--color-ink-dim)]">
				Deposito dikenakan PPh Final 20% (PP 131/2000), SBN 10% (PP 91/2021), sedangkan Reksa Dana 0% bukan objek pajak (UU PPh Pasal 4(3)h).
			</p>
		</div>
	</div>

	<!-- Grid Kartu Zakat & Tax Alpha Tiap Twin -->
	<div class="mt-4 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
		{#each zakatStats as st (st.code)}
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
							class="rounded-full px-2 py-0.5 text-[10px] font-bold {st.isNisabReached ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-500/15 text-slate-400'}"
						>
							{st.isNisabReached ? '✓ Mencapai Nisab' : 'Belum Nisab'}
						</span>
					</div>

					<div class="mt-3 space-y-2 text-xs">
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>Net Worth Th-{year}:</span>
							<strong class="text-[var(--color-ink)]">{rupiahBrief(st.nw)}</strong>
						</div>

						<div class="flex justify-between text-[var(--color-ink-dim)] border-t border-dashed border-[var(--color-line)] pt-1.5">
							<span>Kewajiban Zakat Mal / Th:</span>
							<strong class={st.isNisabReached ? 'text-amber-400' : 'text-[var(--color-ink-dim)]'}>
								{st.isNisabReached ? rupiah(st.zakatAnnual) : 'Rp0'}
							</strong>
						</div>

						{#if st.isNisabReached}
							<div class="flex justify-between text-[11px] text-[var(--color-ink-dim)]">
								<span>Setara per bulan:</span>
								<span>{rupiah(st.zakatMonthly)}/bln</span>
							</div>
						{/if}

						<div class="flex justify-between text-[var(--color-ink-dim)] border-t border-dashed border-[var(--color-line)] pt-1.5">
							<span>Tarif PPh Final Aset:</span>
							<span class="font-semibold text-[var(--color-ink)]">
								{percent(st.taxRate, 0)} ({st.taxRate === 0 ? 'Bebas PPh' : 'Kena Pajak'})
							</span>
						</div>

						{#if st.cumulativeTaxSaved > 0}
							<div class="flex justify-between text-[var(--color-ink-dim)]">
								<span>Hemat PPh vs Deposito:</span>
								<strong class="text-emerald-400">+{rupiahBrief(st.cumulativeTaxSaved)}</strong>
							</div>
						{/if}
					</div>
				</div>

				<div class="mt-3 border-t border-[var(--color-line)]/50 pt-2 text-[10px] text-[var(--color-ink-dim)]">
					{#if st.isNisabReached}
						<span>✨ Harta bersih telah melebihi nisab. Menunaikan zakat membersihkan kekayaan dan memberi keberkahan sosial.</span>
					{:else}
						<span>Fokus kumpulkan dana darurat dan akumulasi aset hingga melampaui batas nisab Rp{rupiahBrief(nisabAmount)}.</span>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>
