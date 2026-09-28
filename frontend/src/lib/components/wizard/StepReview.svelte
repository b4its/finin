<script lang="ts">
	import { sim } from '$lib/stores/simulation.svelte';
	import { rupiahBrief, rupiah } from '$lib/utils/format';
	import type { WizardUiStep } from '$lib/utils/wizard-validation';

	let { onEdit }: { onEdit: (step: WizardUiStep) => void } = $props();

	const incomeLabels: Record<string, string> = {
		salary: 'Gaji tetap',
		allowance: 'Uang saku',
		variable: 'Tidak tetap'
	};
	const presetLabels: Record<string, string> = {
		konservatif: 'Konservatif',
		moderat: 'Moderat',
		optimis: 'Optimis'
	};

	function humanize(type: string): string {
		return type.replace(/_/g, ' ');
	}
</script>

<div class="space-y-5">
	<div>
		<h3 class="text-lg font-bold">Ringkasan sebelum membangun</h3>
		<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
			Periksa kembali. Kamu bisa kembali ke langkah mana pun untuk mengubahnya.
		</p>
	</div>

	<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
		<!-- Penghasilan -->
		<div class="card p-4">
			<div class="flex items-center justify-between">
				<h4 class="text-sm font-semibold">1. Penghasilan</h4>
				<button
					class="text-xs text-[var(--color-accent)] hover:underline"
					onclick={() => onEdit(0)}
				>
					Ubah
				</button>
			</div>
			<dl class="mt-2 space-y-1 text-xs">
				<div class="flex justify-between">
					<dt class="text-[var(--color-ink-dim)]">Tipe</dt>
					<dd>{incomeLabels[sim.input.profile.income_type] ?? sim.input.profile.income_type}</dd>
				</div>
				<div class="flex justify-between">
					<dt class="text-[var(--color-ink-dim)]">Penghasilan/bln</dt>
					<dd class="num">{rupiah(sim.input.profile.income_monthly)}</dd>
				</div>
				<div class="flex justify-between">
					<dt class="text-[var(--color-ink-dim)]">Pengeluaran/bln</dt>
					<dd class="num">{rupiah(sim.input.profile.expense_monthly)}</dd>
				</div>
			</dl>
		</div>

		<!-- Posisi -->
		<div class="card p-4">
			<div class="flex items-center justify-between">
				<h4 class="text-sm font-semibold">2. Posisi</h4>
				<button
					class="text-xs text-[var(--color-accent)] hover:underline"
					onclick={() => onEdit(1)}
				>
					Ubah
				</button>
			</div>
			<dl class="mt-2 space-y-1 text-xs">
				<div class="flex justify-between">
					<dt class="text-[var(--color-ink-dim)]">Usia</dt>
					<dd class="num">{sim.input.profile.age} th</dd>
				</div>
				<div class="flex justify-between">
					<dt class="text-[var(--color-ink-dim)]">Tabungan</dt>
					<dd class="num">{rupiahBrief(sim.input.profile.savings)}</dd>
				</div>
				<div class="flex justify-between">
					<dt class="text-[var(--color-ink-dim)]">Tanggungan/bln</dt>
					<dd class="num">{rupiahBrief(sim.input.profile.dependents_monthly)}</dd>
				</div>
				<div class="flex justify-between">
					<dt class="text-[var(--color-ink-dim)]">Cicilan berjalan</dt>
					<dd class="num">{rupiahBrief(sim.input.profile.existing_debt.monthly_payment)}</dd>
				</div>
			</dl>
		</div>

		<!-- Keputusan -->
		<div class="card p-4 sm:col-span-2">
			<div class="flex items-center justify-between">
				<h4 class="text-sm font-semibold">3. Keputusan yang dibandingkan</h4>
				<button
					class="text-xs text-[var(--color-accent)] hover:underline"
					onclick={() => onEdit(2)}
				>
					Ubah
				</button>
			</div>
			{#if sim.input.decisions.length}
				<ul class="mt-2 space-y-1.5">
					{#each sim.input.decisions as d, i}
						<li class="flex items-center gap-2 text-xs">
							<span
								class="chip !bg-[var(--color-void-3)] !px-1.5 !py-0 !text-[0.65rem] font-bold"
								aria-hidden="true">{i + 1}</span
							>
							<span class="capitalize">{humanize(d.type)}</span>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="mt-2 text-xs text-[var(--color-danger)]">Belum ada keputusan dipilih.</p>
			{/if}
		</div>

		<!-- Asumsi -->
		<div class="card p-4 sm:col-span-2">
			<div class="flex items-center justify-between">
				<h4 class="text-sm font-semibold">4. Asumsi</h4>
				<button
					class="text-xs text-[var(--color-accent)] hover:underline"
					onclick={() => onEdit(3)}
				>
					Ubah
				</button>
			</div>
			<dl class="mt-2 space-y-1 text-xs">
				<div class="flex justify-between">
					<dt class="text-[var(--color-ink-dim)]">Preset</dt>
					<dd>{presetLabels[sim.input.preset] ?? sim.input.preset}</dd>
				</div>
				<div class="flex justify-between">
					<dt class="text-[var(--color-ink-dim)]">Horizon</dt>
					<dd class="num">240 bulan (20 tahun)</dd>
				</div>
			</dl>
		</div>
	</div>
</div>
