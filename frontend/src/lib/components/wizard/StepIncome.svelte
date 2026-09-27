<script lang="ts">
	import CurrencyInput from '$lib/components/ui/CurrencyInput.svelte';
	import { sim } from '$lib/stores/simulation.svelte';

	const incomeTypes = [
		{ value: 'salary', label: 'Gaji tetap', hint: 'Penghasilan bulanan tetap' },
		{ value: 'allowance', label: 'Uang saku', hint: 'Mahasiswa / tunjangan' },
		{ value: 'variable', label: 'Tidak tetap', hint: 'Freelance / ojol / musiman' }
	];

	let deficit = $derived(sim.input.profile.expense_monthly > sim.input.profile.income_monthly);
</script>

<div class="space-y-6">
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
