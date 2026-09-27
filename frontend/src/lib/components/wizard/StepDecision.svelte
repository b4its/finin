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
</div>
