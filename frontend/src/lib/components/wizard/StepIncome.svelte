<script lang="ts">
	import CurrencyInput from '$lib/components/ui/CurrencyInput.svelte';
	import { sim } from '$lib/stores/simulation.svelte';

	const incomeTypes = [
		{ value: 'salary', label: 'Gaji tetap', hint: 'Penghasilan bulanan tetap' },
		{ value: 'allowance', label: 'Uang saku', hint: 'Mahasiswa / tunjangan' },
		{ value: 'variable', label: 'Tidak tetap', hint: 'Freelance / ojol / musiman' }
	];

	interface DemoPersona {
		name: string;
		desc: string;
		icon: string;
		age: number;
		income_type: string;
		income_monthly: number;
		expense_monthly: number;
		savings: number;
		dependents_monthly: number;
		income_range?: { min: number; max: number };
	}

	const DEMO_PERSONAS: DemoPersona[] = [
		{
			name: 'Raka',
			desc: '20 th, Mahasiswa',
			icon: '🎓',
			age: 20,
			income_type: 'allowance',
			income_monthly: 2_500_000,
			expense_monthly: 2_000_000,
			savings: 3_000_000,
			dependents_monthly: 0
		},
		{
			name: 'Sinta',
			desc: '23 th, Fresh Grad',
			icon: '💼',
			age: 23,
			income_type: 'salary',
			income_monthly: 6_000_000,
			expense_monthly: 3_800_000,
			savings: 10_000_000,
			dependents_monthly: 0
		},
		{
			name: 'Dimas',
			desc: '28 th, Generasi Sandwich',
			icon: '🥪',
			age: 28,
			income_type: 'salary',
			income_monthly: 8_000_000,
			expense_monthly: 4_000_000,
			savings: 15_000_000,
			dependents_monthly: 1_500_000
		},
		{
			name: 'Wulan',
			desc: '26 th, Freelancer',
			icon: '🎨',
			age: 26,
			income_type: 'variable',
			income_monthly: 5_500_000,
			expense_monthly: 3_200_000,
			savings: 8_000_000,
			dependents_monthly: 500_000,
			income_range: { min: 4_000_000, max: 7_000_000 }
		}
	];

	function loadPersona(p: DemoPersona) {
		sim.input.profile.age = p.age;
		sim.input.profile.income_type = p.income_type;
		sim.input.profile.income_monthly = p.income_monthly;
		sim.input.profile.expense_monthly = p.expense_monthly;
		sim.input.profile.savings = p.savings;
		sim.input.profile.dependents_monthly = p.dependents_monthly;
		if (p.income_range) {
			sim.input.profile.income_range = p.income_range;
		}
	}

	let deficit = $derived(sim.input.profile.expense_monthly > sim.input.profile.income_monthly);
</script>

<div class="space-y-6">
	<!-- Persona Quick-Fill Banner -->
	<div class="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-3.5">
		<div class="flex items-center justify-between">
			<span class="text-xs font-semibold text-indigo-300"
				>⚡ Contoh Profil Pengguna (1-Klik Isi Cepat)</span
			>
			<span class="text-[10px] text-[var(--color-ink-dim)]">PRD Persona Riset</span>
		</div>
		<div class="mt-2.5 grid grid-cols-2 gap-2 sm:grid-cols-4">
			{#each DEMO_PERSONAS as p}
				<button
					type="button"
					class="flex items-center gap-2 rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] p-2 text-left transition hover:border-[var(--color-accent)]"
					onclick={() => loadPersona(p)}
				>
					<span class="text-base">{p.icon}</span>
					<div class="min-w-0">
						<div class="text-xs font-bold truncate text-[var(--color-ink)]">{p.name}</div>
						<div class="text-[10px] text-[var(--color-ink-dim)] truncate">{p.desc}</div>
					</div>
				</button>
			{/each}
		</div>
	</div>

	<div>
		<h3 class="text-lg font-bold">Penghasilanmu</h3>
		<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
			Kami pakai ini untuk menghitung arus kas dan batas kemampuan bayar (DSR 30%).
		</p>
	</div>

	<div>
		<span class="mb-2 block text-sm font-medium text-[var(--color-ink-dim)]">Jenis penghasilan</span
		>
		<div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
			{#each incomeTypes as t}
				<button
					type="button"
					class="rounded-xl border p-3 text-left transition-colors"
					class:active={sim.input.profile.income_type === t.value}
					class:selected={sim.input.profile.income_type === t.value}
					class:muted={sim.input.profile.income_type !== t.value}
					onclick={() => {
						sim.input.profile.income_type = t.value;
						if (t.value === 'variable' && !sim.input.profile.income_range) {
							sim.input.profile.income_range = {
								min: Math.round(sim.input.profile.income_monthly * 0.7),
								max: Math.round(sim.input.profile.income_monthly * 1.3)
							};
						}
					}}
				>
					<div class="text-sm font-semibold">{t.label}</div>
					<div class="text-xs text-[var(--color-ink-dim)]">{t.hint}</div>
				</button>
			{/each}
		</div>
	</div>

	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
		<CurrencyInput
			bind:value={sim.input.profile.income_monthly}
			label={sim.input.profile.income_type === 'variable'
				? 'Penghasilan rata-rata'
				: 'Penghasilan per bulan'}
			help="Untuk penghasilan tidak tetap, isi rata-rata dan rentang di bawah."
		/>
		<CurrencyInput
			bind:value={sim.input.profile.expense_monthly}
			label="Pengeluaran per bulan"
			help="Termasuk makan, transport, sewa, langganan."
		/>
	</div>

	{#if sim.input.profile.income_type === 'variable' && sim.input.profile.income_range}
		<div class="card p-4">
			<p class="mb-3 text-sm font-medium">Rentang penghasilan (untuk stress test)</p>
			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
				<CurrencyInput bind:value={sim.input.profile.income_range.min} label="Minimum" />
				<CurrencyInput bind:value={sim.input.profile.income_range.max} label="Maksimum" />
			</div>
			<p class="mt-2 text-xs text-[var(--color-ink-dim)]">
				Stress test pakai nilai minimum agar lebih realistis untuk penghasilan tidak tetap.
			</p>
		</div>
	{/if}

	{#if deficit}
		<div class="rounded-xl border border-[var(--color-warn)] bg-amber-500/10 p-3 text-sm">
			⚠️ Pengeluaran lebih besar dari penghasilan. Simulasi akan menunjukkan skenario defisit — ini
			tetap valid, tapi hasilnya perlu diperhatikan.
		</div>
	{/if}
</div>
