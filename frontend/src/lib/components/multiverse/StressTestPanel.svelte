<script lang="ts">
	import Badge from '$lib/components/ui/Badge.svelte';
	import type { Twin } from '$lib/api/types';
	import { rupiahBrief } from '$lib/utils/format';

	let { twins }: { twins: Twin[] } = $props();

	const SHOCKS = [
		{ code: 'income_loss_3m', label: 'Kehilangan penghasilan 3 bulan', icon: '📉' },
		{ code: 'emergency_cost_2x', label: 'Biaya darurat 2× pengeluaran (tahun ke-2)', icon: '🚑' }
	];

	let active = $state<string | null>(null);

	function resultFor(t: Twin, shock: string) {
		return t.stress.find((s) => s.shock === shock);
	}

	let survivors = $derived(
		active ? twins.filter((t) => resultFor(t, active as string)?.survived) : []
	);
</script>

<div class="card p-4">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div>
			<h3 class="text-sm font-semibold">Bagaimana jika?</h3>
			<p class="text-xs text-[var(--color-ink-dim)]">
				Uji ketahanan tiap twin dengan dua guncangan nyata.
			</p>
		</div>
		<div class="flex flex-wrap gap-2">
			{#each SHOCKS as s}
				<button
					class="btn {active === s.code ? 'btn-primary' : 'btn-ghost'}"
					onclick={() => (active = active === s.code ? null : s.code)}
				>
					{s.icon}
					{s.label}
				</button>
			{/each}
		</div>
	</div>

	{#if active}
		<div class="mt-4 space-y-2">
			{#each twins as t (t.code)}
				{@const r = resultFor(t, active)}
				{#if r}
					<div
						class="flex items-center justify-between gap-3 rounded-xl border p-3"
						class:alert-ok={r.survived}
						class:alert-red={!r.survived}
					>
						<div class="flex items-center gap-2">
							<span class="inline-block h-3 w-3 rounded-full" style="background:{t.color}"></span>
							<span class="text-sm font-medium">{t.label}</span>
						</div>
						<div class="flex items-center gap-3">
							<span class="num text-xs text-[var(--color-ink-dim)]">
								kas min {rupiahBrief(r.min_cash)}{r.new_debt > 0
									? ` · utang baru ${rupiahBrief(r.new_debt)}`
									: ''}
							</span>
							<Badge level={r.survived ? 'ok' : 'red'}
								>{r.survived ? 'Bertahan' : 'Tidak bertahan'}</Badge
							>
						</div>
					</div>
				{/if}
			{/each}
			<p class="text-xs text-[var(--color-ink-dim)]">
				“Bertahan” = tidak perlu berutang baru selama guncangan. {survivors.length} dari {twins.length}
				twin bertahan.
			</p>
		</div>
	{:else}
		<p class="mt-4 text-sm text-[var(--color-ink-dim)]">
			Pilih salah satu guncangan di atas untuk melihat hasilnya.
		</p>
	{/if}
</div>
