<script lang="ts">
	import type { Twin, Profile } from '$lib/api/types';
	import { rupiah, rupiahBrief, percent } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let { twins, profile }: { twins: Twin[]; profile?: Profile } = $props();

	type TabMode = 'mal' | 'profesi' | 'cwls';
	let mode = $state<TabMode>('mal');

	let year = $state(10);
	let goldPricePerGram = $state(1_450_000); // Acuan emas Antam 2026
	let ricePricePerKg = $state(16_000); // Acuan beras premium per kg

	// Nisab Zakat Mal: 85 gram emas per tahun
	let nisabMalAnnual = $derived(85 * goldPricePerGram);

	// Nisab Zakat Profesi Bulanan:
	// Standar BAZNAS (SK No. 1/2024 disesuaikan harga emas) = (85 gr emas * harga) / 12
	let nisabProfesiMonthly = $derived(Math.round((85 * goldPricePerGram) / 12));

	// Profil pengguna
	let baseIncomeMonthly = $derived(profile?.income_monthly ?? 10_000_000);
	let baseExpenseMonthly = $derived(profile?.expense_monthly ?? 5_000_000);
	let baseDebtMonthly = $derived(profile?.existing_debt?.monthly_payment ?? 0);

	let profesiMethod = $state<'bruto' | 'neto'>('bruto');

	// CWLS (Cash Waqf Linked Sukuk) parameters
	let cwlsPledgeAmount = $state(5_000_000); // Nominal wakaf uang
	let cwlsYieldRate = $state(0.058); // Imbal hasil kupon sosial ~5.8% p.a.
	let cwlsAnnualYield = $derived(cwlsPledgeAmount * cwlsYieldRate);
	let scholarshipCostPerStudent = 2_500_000; // Biaya beasiswa pendidikan dhuafa / th
	let scholarshipBeneficiaries = $derived((cwlsAnnualYield / scholarshipCostPerStudent).toFixed(1));

	// Perhitungan Zakat Mal & Tax Alpha
	let malStats = $derived(
		twins.map((t) => {
			const pt = t.yearly_series.find((p) => p.year === year) ?? t.yearly_series[t.yearly_series.length - 1];
			const nw = pt?.net_worth ?? 0;
			const isNisabReached = nw >= nisabMalAnnual;
			const zakatAnnual = isNisabReached ? nw * 0.025 : 0;
			const zakatMonthly = zakatAnnual / 12;

			// Hitung Tax Alpha penghematan PPh Final vs Deposito 20%
			const cfg = t.config ?? {};
			const inst = (cfg.instrument as string) || 'money_market';
			let taxRate = 0.2; // baseline deposito 20%
			if (inst === 'bond') taxRate = 0.1; // SBN ritel 10%
			if (inst === 'money_market' || inst === 'stock') taxRate = 0.0; // Reksa dana 0%

			const taxSavingsRate = 0.2 - taxRate;
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

	// Perhitungan Zakat Profesi bulanan
	let profesiBase = $derived(
		profesiMethod === 'bruto'
			? baseIncomeMonthly
			: Math.max(0, baseIncomeMonthly - baseExpenseMonthly - baseDebtMonthly)
	);
	let isProfesiNisabReached = $derived(baseIncomeMonthly >= nisabProfesiMonthly);
	let zakatProfesiMonthly = $derived(isProfesiNisabReached ? Math.round(profesiBase * 0.025) : 0);
	let zakatProfesiAnnual = $derived(zakatProfesiMonthly * 12);

	// Penghematan PPh 21 Pasal 22 UU Zakat No. 23/2011 (Tax Deductible Zakat)
	// Asumsi bracket PPh 21 marginal ~15%
	let marginalTaxBracket = 0.15;
	let pph21TaxSavedAnnual = $derived(Math.round(zakatProfesiAnnual * marginalTaxBracket));
</script>

<div class="card p-5">
	<!-- Tab Bar & Header -->
	<div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4">
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🌙</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Islamic Wealth, Zakat & Kepatuhan Pajak RI
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Integrasi Zakat Mal, Zakat Profesi (Fatwa MUI No. 3/2003), Tax Alpha PPh Final, dan Cash Waqf Linked Sukuk (Kemenkeu & BWI).
			</p>
		</div>

		<!-- Navigasi Mode Tab -->
		<div class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs">
			<button
				class="rounded-md px-3 py-1 font-semibold transition {mode === 'mal' ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]'}"
				onclick={() => (mode = 'mal')}
			>
				Zakat Mal & PPh Final
			</button>
			<button
				class="rounded-md px-3 py-1 font-semibold transition {mode === 'profesi' ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]'}"
				onclick={() => (mode = 'profesi')}
			>
				Zakat Profesi (Gaji)
			</button>
			<button
				class="rounded-md px-3 py-1 font-semibold transition {mode === 'cwls' ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]'}"
				onclick={() => (mode = 'cwls')}
			>
				Wakaf Sukuk (CWLS)
			</button>
		</div>
	</div>

	<!-- TAB 1: ZAKAT MAL & TAX ALPHA PPH FINAL -->
	{#if mode === 'mal'}
		<div class="mt-4 flex flex-wrap items-center justify-between gap-3">
			<div class="flex items-center gap-2">
				<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Horizon Proyeksi:</span>
				<div class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs">
					{#each [5, 10, 20] as y}
						<button
							class="rounded-md px-2.5 py-1 font-semibold transition {year === y ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-ink-dim)]'}"
							onclick={() => (year = y)}
						>
							Th-{y}
						</button>
					{/each}
				</div>
			</div>

			<div class="flex items-center gap-2 text-xs">
				<span class="text-[var(--color-ink-dim)]">Harga Emas Antam:</span>
				<div class="flex items-center gap-1 rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] px-2 py-1">
					<span class="text-[var(--color-ink-dim)]">Rp</span>
					<input
						type="number"
						class="w-24 bg-transparent font-mono text-xs text-[var(--color-ink)] focus:outline-none"
						bind:value={goldPricePerGram}
						step="10000"
					/>
					<span class="text-[10px] text-[var(--color-ink-dim)]">/gr</span>
				</div>
			</div>
		</div>

		<!-- Info Bar Nisab Emas & Pajak Final -->
		<div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
			<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
				<div class="flex items-center justify-between text-xs">
					<span class="font-bold text-[var(--color-ink)]">Ambang Nisab Zakat Mal (85 gr Emas)</span>
					<span class="rounded-full bg-amber-500/10 px-2 py-0.5 font-bold text-amber-400">
						{rupiah(nisabMalAnnual)}
					</span>
				</div>
				<p class="mt-1 text-[11px] text-[var(--color-ink-dim)]">
					Berdasarkan ketentuan BAZNAS (85 gr emas × Rp{goldPricePerGram.toLocaleString('id-ID')}/gr). Wajib ditunaikan 2,5% per tahun apabila telah mencapai haul 1 tahun qamariyah dan di atas nisab.
				</p>
			</div>

			<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
				<div class="flex items-center justify-between text-xs">
					<span class="font-bold text-[var(--color-ink)]">Tax Alpha Investasi Indonesia</span>
					<span class="rounded-full bg-emerald-500/10 px-2 py-0.5 font-bold text-emerald-400">
						Hemat 10%–20% PPh Final
					</span>
				</div>
				<p class="mt-1 text-[11px] text-[var(--color-ink-dim)]">
					Deposito dikenakan PPh Final 20% (PP 131/2000), SBN/Sukuk 10% (PP 91/2021), sedangkan Reksa Dana 0% bukan objek pajak (UU PPh Pasal 4(3)h).
				</p>
			</div>
		</div>

		<!-- Grid Kartu Zakat & Tax Alpha Tiap Twin -->
		<div class="mt-4 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
			{#each malStats as st (st.code)}
				<div
					class="flex flex-col justify-between rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4"
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

							<div class="flex justify-between border-t border-dashed border-[var(--color-line)] pt-1.5 text-[var(--color-ink-dim)]">
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

							<div class="flex justify-between border-t border-dashed border-[var(--color-line)] pt-1.5 text-[var(--color-ink-dim)]">
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
							<span>Fokus kumpulkan dana darurat dan akumulasi aset hingga melampaui batas nisab Rp{rupiahBrief(nisabMalAnnual)}.</span>
						{/if}
					</div>
				</div>
			{/each}
		</div>

	<!-- TAB 2: ZAKAT PROFESI / PENGHASILAN BULANAN (FATWA MUI 3/2003) -->
	{:else if mode === 'profesi'}
		<div class="mt-4 space-y-4">
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
				<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
					<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Gaji / Penghasilan Bulanan</span>
					<div class="mt-1 text-lg font-bold text-[var(--color-ink)]">{rupiah(baseIncomeMonthly)}</div>
					<div class="mt-0.5 text-[11px] text-[var(--color-ink-dim)]">
						{isProfesiNisabReached ? '✓ Di atas ambang nisab BAZNAS' : '⚠️ Belum mencapai batas nisab bulanan'}
					</div>
				</div>

				<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
					<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Nisab Bulanan (BAZNAS RI)</span>
					<div class="mt-1 text-lg font-bold text-amber-400">{rupiah(nisabProfesiMonthly)}</div>
					<div class="mt-0.5 text-[11px] text-[var(--color-ink-dim)]">
						Setara 85 gr emas/12 bulan (SK BAZNAS No. 1/2024)
					</div>
				</div>

				<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
					<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Pengurang PPh 21 (UU 23/2011)</span>
					<div class="mt-1 text-lg font-bold text-emerald-400">+{rupiah(pph21TaxSavedAnnual)}/th</div>
					<div class="mt-0.5 text-[11px] text-[var(--color-ink-dim)]">
						Estimasi hemat pajak penghasilan via bukti setor zakat
					</div>
				</div>
			</div>

			<!-- Opsi Metode Penghitungan Zakat Profesi -->
			<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4">
				<div class="flex flex-wrap items-center justify-between gap-3">
					<div>
						<h4 class="text-xs font-bold text-[var(--color-ink)]">Metode Kaidah Fiqih Zakat Profesi</h4>
						<p class="text-[11px] text-[var(--color-ink-dim)]">
							Fatwa MUI No. 3/2003 membolehkan zakat dihitung dari penghasilan kotor (bruto) atau bersih setelah kebutuhan pokok (neto).
						</p>
					</div>
					<div class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] p-0.5 text-xs">
						<button
							class="rounded-md px-3 py-1 font-semibold transition {profesiMethod === 'bruto' ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-ink-dim)]'}"
							onclick={() => (profesiMethod = 'bruto')}
						>
							Pendapatan Bruto (2,5%)
						</button>
						<button
							class="rounded-md px-3 py-1 font-semibold transition {profesiMethod === 'neto' ? 'bg-[var(--color-accent)] text-white' : 'text-[var(--color-ink-dim)]'}"
							onclick={() => (profesiMethod = 'neto')}
						>
							Neto (Potong Biaya Pokok)
						</button>
					</div>
				</div>

				<div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
					<div class="space-y-2 rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] p-3 text-xs">
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>Dasar Pengenaan Zakat (Bulanan):</span>
							<strong class="text-[var(--color-ink)]">{rupiah(profesiBase)}</strong>
						</div>
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>Tarif Zakat Profesi:</span>
							<strong class="text-[var(--color-ink)]">2,5%</strong>
						</div>
						<div class="flex justify-between border-t border-[var(--color-line)] pt-2 font-bold">
							<span class="text-[var(--color-ink)]">Kewajiban Zakat Profesi / Bulan:</span>
							<span class="text-amber-400">{rupiah(zakatProfesiMonthly)}</span>
						</div>
						<div class="flex justify-between text-[11px] text-[var(--color-ink-dim)]">
							<span>Kewajiban per Tahun (12 bulan):</span>
							<span>{rupiah(zakatProfesiAnnual)}</span>
						</div>
					</div>

					<div class="flex flex-col justify-between rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs">
						<div>
							<div class="flex items-center gap-1.5 font-bold text-emerald-400">
								<span>🏛️</span>
								<span>Fasilitas Pengurang Pajak Penghasilan (UU No. 23/2011 Ps. 22)</span>
							</div>
							<p class="mt-1 text-[11px] leading-relaxed text-[var(--color-ink-dim)]">
								Zakat yang dibayarkan melalui Badan Amil Zakat Nasional (BAZNAS) atau LAZ resmi yang diakui pemerintah merupakan <strong class="text-[var(--color-ink)]">faktor pengurang penghasilan bruto</strong> dalam pelaporan SPT Tahunan PPh Orang Pribadi (Formulir 1770 S).
							</p>
						</div>
						<div class="mt-2 rounded border border-emerald-500/30 bg-emerald-500/10 p-2 text-[11px] text-emerald-300">
							💡 Dengan menyalurkan zakat {rupiah(zakatProfesiAnnual)}/th secara resmi, beban pajak PPh 21 Anda berpotensi berkurang hingga <strong>{rupiah(pph21TaxSavedAnnual)}/tahun</strong>.
						</div>
					</div>
				</div>
			</div>
		</div>

	<!-- TAB 3: CASH WAQF LINKED SUKUK (CWLS) / SUKUK WAKAF RITEL -->
	{:else if mode === 'cwls'}
		<div class="mt-4 space-y-4">
			<div class="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-4">
				<div class="flex items-start gap-3">
					<span class="text-2xl">🕌</span>
					<div>
						<h4 class="text-sm font-bold text-[var(--color-ink)]">
							Sukuk Wakaf Ritel (Cash Waqf Linked Sukuk - CWLS)
						</h4>
						<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
							Inovasi instrumen sosial-investasi resmi Kementerian Keuangan RI, Bank Indonesia, dan Badan Wakaf Indonesia (BWI). Pokok dana aman 100% dijamin negara, sedangkan seluruh imbal hasil kupon dialokasikan langsung untuk kemaslahatan sosial (beasiswa, faskes duafa, renovasi madrasah).
						</p>
					</div>
				</div>
			</div>

			<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
				<!-- Input Komitmen Wakaf Uang -->
				<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-4 sm:col-span-1">
					<span class="block text-xs font-semibold text-[var(--color-ink-dim)]">
						Nominal Wakaf Uang (CWLS)
					</span>
					<div class="mt-2 flex items-center gap-1 rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] px-3 py-2">
						<span class="text-xs text-[var(--color-ink-dim)]">Rp</span>
						<input
							type="number"
							class="w-full bg-transparent font-mono text-sm font-bold text-[var(--color-ink)] focus:outline-none"
							bind:value={cwlsPledgeAmount}
							min="1000000"
							step="1000000"
						/>
					</div>
					<div class="mt-2 flex flex-wrap gap-1">
						{#each [1_000_000, 5_000_000, 10_000_000, 25_000_000] as amt}
							<button
								type="button"
								class="rounded bg-[var(--color-void-2)] px-2 py-0.5 text-[10px] text-[var(--color-ink-dim)] hover:bg-[var(--color-void-3)]"
								onclick={() => (cwlsPledgeAmount = amt)}
							>
								{rupiahBrief(amt)}
							</button>
						{/each}
					</div>
					<p class="mt-3 text-[10px] text-[var(--color-ink-dim)]">
						Wakaf uang temporer (tenor 2–3 tahun). Pokok 100% kembali utuh kepada wakif saat jatuh tempo.
					</p>
				</div>

				<!-- Dampak Sosial & Kupon Berkelanjutan -->
				<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4 sm:col-span-2">
					<span class="text-xs font-bold text-[var(--color-ink)]">Dampak Sosial Kupon Wakaf (Social Yield)</span>
					<div class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 text-xs">
						<div class="rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] p-3">
							<span class="text-[var(--color-ink-dim)]">Imbal Hasil Kupon Sosial (5,8% p.a.):</span>
							<div class="mt-1 text-base font-bold text-teal-400">{rupiah(cwlsAnnualYield)} / tahun</div>
							<div class="text-[10px] text-[var(--color-ink-dim)]">({rupiah(cwlsAnnualYield / 12)} / bulan dialirkan ke nazhir)</div>
						</div>

						<div class="rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] p-3">
							<span class="text-[var(--color-ink-dim)]">Pemberian Beasiswa Pelajar Dhuafa:</span>
							<div class="mt-1 text-base font-bold text-amber-400">{scholarshipBeneficiaries} Anak / Tahun</div>
							<div class="text-[10px] text-[var(--color-ink-dim)]">Biaya beasiswa penuh standar Rp2,5 jt/siswa</div>
						</div>
					</div>

					<div class="mt-3 space-y-1.5 text-[11px] text-[var(--color-ink-dim)]">
						<div class="flex items-center gap-2">
							<span class="text-emerald-400">✓</span>
							<span><strong>100% Risk-Free Pokok:</strong> Dijamin penuh oleh Surat Berharga Syariah Negara (SBSN).</span>
						</div>
						<div class="flex items-center gap-2">
							<span class="text-emerald-400">✓</span>
							<span><strong>Sertifikat Wakaf Uang (SWU):</strong> Diterbitkan secara resmi oleh Kementerian Agama & BWI.</span>
						</div>
						<div class="flex items-center gap-2">
							<span class="text-emerald-400">✓</span>
							<span><strong>Amal Jariah Abadi:</strong> Pahala kemanfaatan sosial terus mengalir tanpa mengurangi modal finansial Anda.</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
