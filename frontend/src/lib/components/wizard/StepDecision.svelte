<script lang="ts">
	import CurrencyInput from '$lib/components/ui/CurrencyInput.svelte';
	import PercentInput from '$lib/components/ui/PercentInput.svelte';
	import Toggle from '$lib/components/ui/Toggle.svelte';
	import RegulatoryFlag from './RegulatoryFlag.svelte';
	import { sim } from '$lib/stores/simulation.svelte';
	import type { Decision } from '$lib/api/types';

	const TEMPLATES = [
		{ type: 'loan_vs_save', title: 'Pinjol/Paylater vs Nabung Dulu', icon: '💳', twins: 'A & B' },
		{ type: 'study_vs_work', title: 'S2 vs Kerja + Upskilling', icon: '🎓', twins: 'C & D' },
		{
			type: 'emergency_vs_invest',
			title: 'Dana Darurat Dulu vs Langsung Investasi',
			icon: '🛡️',
			twins: 'E & F'
		},
		{
			type: 'kpr_vs_rent',
			title: 'Beli Rumah KPR vs Sewa & Investasi',
			icon: '🏠',
			twins: 'G & H'
		},
		{
			type: 'vehicle_lease_vs_cash',
			title: 'Kredit Kendaraan vs Bekas Tunai',
			icon: '🚗',
			twins: 'I & J'
		},
		{
			type: 'wedding_grand_vs_intimate',
			title: 'Pesta Nikah Mewah vs Intim & Modal Keluarga',
			icon: '💍',
			twins: 'K & L'
		},
		{
			type: 'franchise_vs_passive_invest',
			title: 'Franchise Mikro (KUR) vs Investasi Dividen Pasif',
			icon: '🏪',
			twins: 'M & N'
		},
		{
			type: 'child_education_unitlink_vs_diy',
			title: 'Pendidikan Anak: Unit Link vs Tabungan Mandiri',
			icon: '🎓',
			twins: 'O & P'
		}
	];

	const instruments = [
		{ value: 'savings', label: 'Tabungan bank (~1%/th)' },
		{ value: 'deposit', label: 'Deposito (~3,5%/th)' },
		{ value: 'money_market', label: 'Reksa dana pasar uang (~4,5%/th)' },
		{ value: 'bond', label: 'SBN ritel (~6,8%/th)' },
		{ value: 'stock', label: 'Reksa dana indeks saham (~9%/th, berisiko)' }
	];

	let selected = $derived(sim.input.decisions.map((d) => d.type));

	function defaultDecision(type: string): Decision {
		if (type === 'loan_vs_save')
			return {
				type,
				loan: {
					kind: 'pinjol',
					amount: 2_000_000,
					tenor_months: 3,
					rate_daily: 0.003,
					penalty_daily: null
				},
				save: { monthly: 500_000, instrument: 'money_market' }
			};
		if (type === 'study_vs_work')
			return {
				type,
				study: {
					years: 2,
					total_cost: 80_000_000,
					part_time_work: false,
					part_time_monthly: 0,
					salary_premium: 0.15
				},
				work: { upskill_monthly: 300_000, skill_premium: 0.1, premium_after_months: 12 }
			};
		if (type === 'kpr_vs_rent')
			return {
				type,
				kpr: {
					property_price: 500_000_000,
					down_payment_pct: 0.2,
					interest_rate_annual: 0.08,
					tenor_years: 15,
					property_appreciation_annual: 0.04
				},
				rent: {
					rent_monthly: 2_500_000,
					invest_instrument: 'bond'
				}
			};
		if (type === 'vehicle_lease_vs_cash')
			return {
				type,
				vehicle_lease: {
					vehicle_price: 30_000_000,
					down_payment_pct: 0.2,
					interest_rate_annual: 0.12,
					tenor_months: 36,
					depreciation_annual: 0.15
				},
				vehicle_cash: {
					used_vehicle_price: 12_000_000,
					invest_instrument: 'stock'
				}
			};
		if (type === 'wedding_grand_vs_intimate')
			return {
				type,
				wedding_grand: {
					reception_cost: 150_000_000,
					savings_used: 50_000_000,
					loan_amount: 100_000_000,
					interest_rate_annual: 0.12,
					tenor_months: 36
				},
				wedding_intimate: {
					intimate_cost: 25_000_000,
					invest_instrument: 'stock'
				}
			};
		if (type === 'franchise_vs_passive_invest')
			return {
				type,
				franchise: {
					franchise_fee: 75_000_000,
					savings_used: 25_000_000,
					kur_loan_amount: 50_000_000,
					kur_interest_rate_annual: 0.06,
					kur_tenor_months: 36,
					monthly_net_profit: 4_500_000
				},
				passive_invest: {
					invest_instrument: 'bond'
				}
			};
		if (type === 'child_education_unitlink_vs_diy')
			return {
				type,
				child_education_unitlink: {
					monthly_premium: 1_500_000,
					target_years: 15,
					acquisition_fee_pct_y1: 0.6,
					acquisition_fee_pct_y2: 0.3,
					acquisition_fee_pct_y3: 0.15,
					invest_instrument: 'stock'
				},
				child_education_diy: {
					term_life_premium_monthly: 250_000,
					invest_instrument: 'stock'
				}
			};
		return { type, emergency: { target_months: 6, invest_monthly: 1_000_000 } };
	}

	function toggleTemplate(type: string) {
		const idx = sim.input.decisions.findIndex((d) => d.type === type);
		if (idx >= 0) {
			sim.input.decisions.splice(idx, 1);
		} else if (sim.input.decisions.length < 2) {
			sim.input.decisions = [...sim.input.decisions, defaultDecision(type)];
		}
	}

	function decisionOf(type: string): Decision | undefined {
		return sim.input.decisions.find((d) => d.type === type);
	}
</script>

<div class="space-y-6">
	<div>
		<h3 class="text-lg font-bold">Pilih keputusan yang mau dibandingkan</h3>
		<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
			Pilih 1–2 template. Setiap template menghasilkan dua "kembaran" dari dirimu di masa depan.
		</p>
	</div>

	<div class="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
		{#each TEMPLATES as t}
			<button
				type="button"
				class="rounded-xl border p-3 text-left transition-colors"
				class:active={selected.includes(t.type)}
				class:selected={selected.includes(t.type)}
				class:muted={!selected.includes(t.type)}
				class:opacity-50={!selected.includes(t.type) && sim.input.decisions.length >= 2}
				onclick={() => toggleTemplate(t.type)}
			>
				<div class="text-xl">{t.icon}</div>
				<div class="mt-1 text-sm font-semibold">{t.title}</div>
				<div class="text-xs text-[var(--color-ink-dim)]">Twin {t.twins}</div>
			</button>
		{/each}
	</div>

	{#if selected.includes('loan_vs_save')}
		{@const d = decisionOf('loan_vs_save')!}
		{@const loan = d.loan!}
		{@const save = d.save!}
		<div class="card space-y-4 p-4">
			<p class="text-sm font-semibold">💳 Pinjol/Paylater vs Nabung Dulu</p>
			<div>
				<span class="mb-2 block text-sm text-[var(--color-ink-dim)]">Jenis pinjaman</span>
				<div class="flex gap-2">
					{#each [{ v: 'pinjol', l: 'Pinjol' }, { v: 'paylater', l: 'Paylater' }] as o}
						<button
							type="button"
							class="chip"
							class:active={loan.kind === o.v}
							onclick={() => (loan.kind = o.v)}>{o.l}</button
						>
					{/each}
				</div>
			</div>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
				<CurrencyInput bind:value={loan.amount} label="Nominal pinjaman" />
				<label class="block">
					<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
						>Tenor (bulan)</span
					>
					<input
						class="input num"
						type="number"
						min="1"
						max="60"
						value={loan.tenor_months}
						oninput={(e) =>
							(loan.tenor_months = parseInt((e.target as HTMLInputElement).value) || 1)}
					/>
				</label>
				<PercentInput
					bind:value={loan.rate_daily}
					label="Bunga per hari"
					step={0.01}
					max={5}
					help="Bunga harian. Batas OJK: 0,3%/hari (tenor ≤6 bln)."
				/>
			</div>
			<RegulatoryFlag
				kind={loan.kind}
				amount={loan.amount}
				tenorMonths={loan.tenor_months}
				rateDaily={loan.rate_daily}
				incomeMonthly={sim.input.profile.income_monthly}
				existingPayment={sim.input.profile.existing_debt.monthly_payment}
			/>
			<div class="border-t border-[var(--color-line)] pt-4">
				<p class="mb-3 text-sm font-semibold">Skenario B — Si Penabung</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<CurrencyInput bind:value={save.monthly} label="Tabungan per bulan" />
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Instrumen</span
						>
						<select class="input" bind:value={save.instrument}>
							{#each instruments as i}<option value={i.value}>{i.label}</option>{/each}
						</select>
					</label>
				</div>
			</div>
		</div>
	{/if}

	{#if selected.includes('study_vs_work')}
		{@const d = decisionOf('study_vs_work')!}
		{@const study = d.study!}
		{@const work = d.work!}
		<div class="card space-y-4 p-4">
			<p class="text-sm font-semibold">🎓 S2 vs Kerja + Upskilling</p>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
				<label class="block">
					<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
						>Durasi S2 (tahun)</span
					>
					<input
						class="input num"
						type="number"
						min="1"
						max="6"
						value={study.years}
						oninput={(e) => (study.years = parseInt((e.target as HTMLInputElement).value) || 1)}
					/>
				</label>
				<CurrencyInput bind:value={study.total_cost} label="Biaya total S2" />
				<PercentInput
					bind:value={study.salary_premium}
					label="Premi gaji S2"
					step={1}
					help="Default +15% (rentang 8–25%)."
				/>
			</div>
			<Toggle bind:checked={study.part_time_work} label="Kuliah sambil kerja (part-time)" />
			{#if study.part_time_work}
				<CurrencyInput
					bind:value={study.part_time_monthly}
					label="Penghasilan part-time per bulan"
				/>
			{/if}
			<div class="border-t border-[var(--color-line)] pt-4">
				<p class="mb-3 text-sm font-semibold">Skenario D — Si Praktisi</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
					<CurrencyInput bind:value={work.upskill_monthly} label="Biaya kursus/bulan" />
					<PercentInput bind:value={work.skill_premium} label="Premi keahlian" step={1} />
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Berlaku setelah (bulan)</span
						>
						<input
							class="input num"
							type="number"
							min="1"
							value={work.premium_after_months}
							oninput={(e) =>
								(work.premium_after_months = parseInt((e.target as HTMLInputElement).value) || 12)}
						/>
					</label>
				</div>
			</div>
		</div>
	{/if}

	{#if selected.includes('emergency_vs_invest')}
		{@const d = decisionOf('emergency_vs_invest')!}
		{@const em = d.emergency!}
		<div class="card space-y-4 p-4">
			<p class="text-sm font-semibold">🛡️ Dana Darurat Dulu vs Langsung Investasi</p>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				<label class="block">
					<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
						>Target dana darurat (bulan)</span
					>
					<input
						class="input num"
						type="number"
						min="3"
						max="6"
						value={em.target_months}
						oninput={(e) =>
							(em.target_months = parseInt((e.target as HTMLInputElement).value) || 6)}
					/>
					<p class="mt-1.5 text-xs text-[var(--color-ink-dim)]">
						Rekomendasi 3–6 bulan biaya hidup.
					</p>
				</label>
				<CurrencyInput bind:value={em.invest_monthly} label="Investasi per bulan" />
			</div>
		</div>
	{/if}

	{#if selected.includes('kpr_vs_rent')}
		{@const d = decisionOf('kpr_vs_rent')!}
		{@const kpr = d.kpr!}
		{@const rent = d.rent!}
		<div class="card space-y-4 p-4">
			<div class="flex items-center justify-between">
				<p class="text-sm font-semibold">🏠 Beli Rumah KPR vs Sewa & Investasi</p>
			</div>

			<div class="space-y-4">
				<p class="text-sm font-semibold text-emerald-400">Skenario G — Si Pemilik Rumah (KPR)</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
					<CurrencyInput bind:value={kpr.property_price} label="Harga Properti / Rumah" />
					<PercentInput bind:value={kpr.down_payment_pct} label="Uang Muka (DP)" step={5} />
					<PercentInput
						bind:value={kpr.interest_rate_annual}
						label="Suku Bunga KPR / Tahun"
						step={0.5}
					/>
				</div>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Tenor KPR (tahun)</span
						>
						<input
							class="input num"
							type="number"
							min="5"
							max="30"
							value={kpr.tenor_years}
							oninput={(e) =>
								(kpr.tenor_years = parseInt((e.target as HTMLInputElement).value) || 15)}
						/>
					</label>
					<PercentInput
						bind:value={kpr.property_appreciation_annual}
						label="Apresiasi Nilai Properti / Tahun"
						step={0.5}
					/>
				</div>
			</div>

			<div class="border-t border-[var(--color-line)] pt-4">
				<p class="mb-3 text-sm font-semibold text-pink-400">
					Skenario H — Si Pengontrak & Investor
				</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<CurrencyInput bind:value={rent.rent_monthly} label="Biaya Sewa / Kontrak Bulanan" />
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Instrumen Investasi Selisih</span
						>
						<select class="input" bind:value={rent.invest_instrument}>
							{#each instruments as ins}
								<option value={ins.value}>{ins.label}</option>
							{/each}
						</select>
					</label>
				</div>
				<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
					Dana DP tetap berada di tabungan/investasi, dan selisih antara cicilan KPR dengan biaya
					sewa diinvestasikan secara disiplin tiap bulan.
				</p>
			</div>
		</div>
	{/if}

	{#if selected.includes('vehicle_lease_vs_cash')}
		{@const d = decisionOf('vehicle_lease_vs_cash')!}
		{@const lease = d.vehicle_lease!}
		{@const cash = d.vehicle_cash!}
		<div class="card space-y-4 p-4">
			<p class="text-sm font-semibold">🚗 Kredit Kendaraan (Leasing OJK) vs Bekas Tunai</p>
			<div>
				<p class="mb-3 text-sm font-semibold text-orange-400">
					Skenario I — Si Pengkredit Leasing (Unit Baru)
				</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<CurrencyInput bind:value={lease.vehicle_price} label="Harga Kendaraan Baru" />
					<PercentInput bind:value={lease.down_payment_pct} label="Uang Muka (DP)" step={5} />
				</div>
				<div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
					<PercentInput
						bind:value={lease.interest_rate_annual}
						label="Suku Bunga Leasing / Tahun"
						step={1}
						help="Sesuai leasing OJK (10–18%/tahun)."
					/>
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Tenor (bulan)</span
						>
						<input
							class="input num"
							type="number"
							min="12"
							max="60"
							value={lease.tenor_months}
							oninput={(e) =>
								(lease.tenor_months = parseInt((e.target as HTMLInputElement).value) || 36)}
						/>
					</label>
					<PercentInput
						bind:value={lease.depreciation_annual}
						label="Penyusutan Nilai / Tahun"
						step={1}
						help="Depresiasi motor/mobil ~10–15%/thn."
					/>
				</div>
			</div>

			<div class="border-t border-[var(--color-line)] pt-4">
				<p class="mb-3 text-sm font-semibold text-cyan-400">
					Skenario J — Si Pembeli Bekas & Investor
				</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<CurrencyInput bind:value={cash.used_vehicle_price} label="Harga Beli Bekas Tunai" />
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Instrumen Investasi Selisih Cicilan</span
						>
						<select class="input" bind:value={cash.invest_instrument}>
							{#each instruments as ins}
								<option value={ins.value}>{ins.label}</option>
							{/each}
						</select>
					</label>
				</div>
				<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
					Membeli kendaraan bekas layak pakai secara tunai (bebas cicilan utang bulanan), dan
					selisih cicilan bulanan diinvestasikan secara disiplin tiap tanggal gajian.
				</p>
			</div>
		</div>
	{/if}

	{#if selected.includes('wedding_grand_vs_intimate')}
		{@const d = decisionOf('wedding_grand_vs_intimate')!}
		{@const grand = d.wedding_grand!}
		{@const intimate = d.wedding_intimate!}
		<div class="card space-y-4 p-4">
			<p class="text-sm font-semibold">💍 Pesta Pernikahan Mewah (KTA) vs Nikah Intim & Modal Keluarga</p>
			<div>
				<p class="mb-3 text-sm font-semibold text-rose-400">
					Skenario K — Si Pesta Akbar (Resepsi Besar & Utang KTA)
				</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
					<CurrencyInput bind:value={grand.reception_cost} label="Total Biaya Resepsi Mewah" />
					<CurrencyInput bind:value={grand.savings_used} label="Porsi Tabungan Sendiri" />
					<CurrencyInput bind:value={grand.loan_amount} label="Porsi Pinjaman KTA Bank" />
				</div>
				<div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Tenor KTA (bulan)</span
						>
						<input
							class="input num"
							type="number"
							min="6"
							max="60"
							value={grand.tenor_months}
							oninput={(e) =>
								(grand.tenor_months = parseInt((e.target as HTMLInputElement).value) || 36)}
						/>
					</label>
					<PercentInput
						bind:value={grand.interest_rate_annual}
						label="Suku Bunga KTA Bank / Tahun"
						step={1}
						help="Suku bunga komersial bank ~10–18%/tahun."
					/>
				</div>
			</div>

			<div class="border-t border-[var(--color-line)] pt-4">
				<p class="mb-3 text-sm font-semibold text-teal-400">
					Skenario L — Si Intim & Modal Keluarga
				</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<CurrencyInput bind:value={intimate.intimate_cost} label="Biaya Nikah Intim / KUA (Tunai)" />
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Instrumen Investasi Selisih Cicilan</span
						>
						<select class="input" bind:value={intimate.invest_instrument}>
							{#each instruments as ins}
								<option value={ins.value}>{ins.label}</option>
							{/each}
						</select>
					</label>
				</div>
				<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
					Pernikahan sakral intim/KUA secara tunai tanpa utang KTA baru. Sisa tabungan dan selisih cicilan
					bulanan KTA diinvestasikan penuh ke portofolio modal rumah tangga.
				</p>
			</div>
		</div>
	{/if}

	{#if selected.includes('franchise_vs_passive_invest')}
		{@const d = decisionOf('franchise_vs_passive_invest')!}
		{@const fran = d.franchise!}
		{@const pass = d.passive_invest!}
		<div class="card space-y-4 p-4">
			<p class="text-sm font-semibold">🏪 Franchise Mikro (KUR) vs Portofolio Dividen Pasif</p>
			<div>
				<p class="mb-3 text-sm font-semibold text-purple-400">
					Skenario M — Si Pebisnis Waralaba (Modal Usaha + Pinjaman KUR)
				</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
					<CurrencyInput bind:value={fran.franchise_fee} label="Total Modal Awal Waralaba" />
					<CurrencyInput bind:value={fran.savings_used} label="Porsi Modal Sendiri (Tabungan)" />
					<CurrencyInput bind:value={fran.kur_loan_amount} label="Pinjaman KUR Bank (Subsidi 6%/th)" />
				</div>
				<div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Tenor KUR (bulan)</span
						>
						<input
							class="input num"
							type="number"
							min="12"
							max="60"
							value={fran.kur_tenor_months}
							oninput={(e) =>
								(fran.kur_tenor_months = parseInt((e.target as HTMLInputElement).value) || 36)}
						/>
					</label>
					<CurrencyInput bind:value={fran.monthly_net_profit} label="Estimasi Laba Bersih Usaha / Bulan" />
				</div>
			</div>

			<div class="border-t border-[var(--color-line)] pt-4">
				<p class="mb-3 text-sm font-semibold text-emerald-400">
					Skenario N — Si Investor Pasif & Dividen
				</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Instrumen Investasi Pasif</span
						>
						<select class="input" bind:value={pass.invest_instrument}>
							{#each instruments as ins}
								<option value={ins.value}>{ins.label}</option>
							{/each}
						</select>
					</label>
				</div>
				<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
					Tidak mengambil risiko operasional bisnis dan bebas cicilan utang KUR. Tabungan tetap utuh di portofolio, dan alokasi dana setara cicilan dialihkan tiap bulan ke instrumen pasif.
				</p>
			</div>
		</div>
	{/if}

	{#if selected.includes('child_education_unitlink_vs_diy')}
		{@const d = decisionOf('child_education_unitlink_vs_diy')!}
		{@const ul = d.child_education_unitlink!}
		{@const diy = d.child_education_diy!}
		<div class="card space-y-4 p-4">
			<p class="text-sm font-semibold">🎓 Dana Pendidikan Anak: Unit Link vs Tabungan Mandiri + Asuransi Murni</p>
			<div>
				<p class="mb-3 text-sm font-semibold text-rose-400">
					Skenario O — Si Asuransi Unit Link (PAYDI Terintegrasi)
				</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
					<CurrencyInput bind:value={ul.monthly_premium} label="Premi Unit Link Bulanan" />
					<PercentInput
						bind:value={ul.acquisition_fee_pct_y1}
						label="Beban Akuisisi Th-1 (Beban PAYDI)"
						step={5}
						max={90}
						help="Rerata polis di RI memotong 50-70% premi di tahun pertama untuk komisi agen."
					/>
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Subdana Investasi Polis</span
						>
						<select class="input" bind:value={ul.invest_instrument}>
							{#each instruments as ins}
								<option value={ins.value}>{ins.label}</option>
							{/each}
						</select>
					</label>
				</div>
			</div>

			<div class="border-t border-[var(--color-line)] pt-4">
				<p class="mb-3 text-sm font-semibold text-emerald-400">
					Skenario P — Si Portofolio Mandiri (SBN/Saham) + Asuransi Murni
				</p>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<CurrencyInput bind:value={diy.term_life_premium_monthly} label="Premi Asuransi Jiwa Murni / Bulan" />
					<label class="block">
						<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
							>Instrumen Investasi Mandiri (0% Akuisisi)</span
						>
						<select class="input" bind:value={diy.invest_instrument}>
							{#each instruments as ins}
								<option value={ins.value}>{ins.label}</option>
							{/each}
						</select>
					</label>
				</div>
				<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
					Memisahkan proteksi jiwa dengan asuransi murni (tanpa embel-embel investasi). Sisa alokasi dana
					diinvestasikan 100% secara langsung ke instrumen pasar modal tanpa potongan biaya akuisisi PAYDI.
				</p>
			</div>
		</div>
	{/if}
</div>
