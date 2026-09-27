<script lang="ts">
	import CurrencyInput from '$lib/components/ui/CurrencyInput.svelte';
	import Tooltip from '$lib/components/ui/Tooltip.svelte';
	import { sim } from '$lib/stores/simulation.svelte';

	let dsr = $derived(
		sim.input.profile.income_monthly > 0
			? sim.input.profile.existing_debt.monthly_payment / sim.input.profile.income_monthly
			: 0
	);
</script>

<div class="space-y-6">
	<div>
		<h3 class="text-lg font-bold">Posisi keuanganmu</h3>
		<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
			Termasuk tanggungan keluarga — supaya hasilnya relevan untuk generasi sandwich.
		</p>
	</div>

	<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
		<label class="block">
			<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]">Usia</span>
			<input
				class="input num"
				type="number"
				min="15"
				max="60"
				value={sim.input.profile.age}
				oninput={(e) =>
					(sim.input.profile.age = parseInt((e.target as HTMLInputElement).value) || 22)}
			/>
			<p class="mt-1.5 text-xs text-[var(--color-ink-dim)]">15–60 tahun</p>
		</label>
		<CurrencyInput
			bind:value={sim.input.profile.savings}
			label="Tabungan / kas likuid saat ini"
			help="Uang yang bisa cepat dipakai."
		/>
	</div>

	<CurrencyInput
		bind:value={sim.input.profile.dependents_monthly}
		label="Tanggungan keluarga per bulan"
		help="Kirim ke orang tua, biaya anak, atau anggota keluarga lain."
	/>

	<div class="card p-4">
		<div class="mb-3 flex items-center gap-2">
			<p class="text-sm font-semibold">Utang berjalan (opsional)</p>
			<Tooltip
				text="Sisa pokok dan cicilan bulanan dari utang yang sudah ada, misalnya cicilan motor atau KPR."
			>
				<span class="chip cursor-help">?</span>
			</Tooltip>
		</div>
		<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
			<CurrencyInput
				bind:value={sim.input.profile.existing_debt.principal}
				label="Sisa pokok utang"
			/>
			<CurrencyInput
				bind:value={sim.input.profile.existing_debt.monthly_payment}
				label="Cicilan per bulan"
			/>
		</div>
		<div class="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
			<label class="block">
				<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
					>Bunga tahunan</span
				>
				<input
					class="input num"
					type="number"
					step="0.1"
					value={(sim.input.profile.existing_debt.annual_rate * 100).toString()}
					oninput={(e) =>
						(sim.input.profile.existing_debt.annual_rate =
							(parseFloat((e.target as HTMLInputElement).value) || 0) / 100)}
				/>
			</label>
			<label class="block">
				<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]"
					>Sisa tenor (bulan)</span
				>
				<input
					class="input num"
					type="number"
					min="0"
					value={sim.input.profile.existing_debt.tenor_months}
					oninput={(e) =>
						(sim.input.profile.existing_debt.tenor_months =
							parseInt((e.target as HTMLInputElement).value) || 0)}
				/>
			</label>
		</div>
	</div>

	{#if dsr > 0.3}
		<div class="rounded-xl border border-[var(--color-warn)] bg-amber-500/10 p-3 text-sm">
			⚠️ Cicilan berjalan sudah {(dsr * 100).toFixed(0)}% dari penghasilan — melebihi batas
			kemampuan bayar 30% yang dipakai OJK.
		</div>
	{/if}
</div>
