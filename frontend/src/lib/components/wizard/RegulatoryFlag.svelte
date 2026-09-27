<script lang="ts">
	import Badge from '$lib/components/ui/Badge.svelte';
	import { api } from '$lib/api/client';
	import type { Flag } from '$lib/api/types';

	let {
		kind = 'pinjol',
		amount = 0,
		tenorMonths = 3,
		rateDaily = 0,
		penaltyDaily = null,
		incomeMonthly = 0,
		existingPayment = 0
	}: {
		kind?: string;
		amount?: number;
		tenorMonths?: number;
		rateDaily?: number;
		penaltyDaily?: number | null;
		incomeMonthly?: number;
		existingPayment?: number;
	} = $props();

	let flags = $state<Flag[]>([]);
	let cap = $state(0.003);
	let dsr = $state(0);
	let timer: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		// dependensi reaktif
		const payload = {
			kind,
			amount,
			tenor_months: tenorMonths,
			rate_daily: rateDaily,
			penalty_daily: penaltyDaily,
			income_monthly: incomeMonthly,
			existing_payment: existingPayment
		};
		clearTimeout(timer);
		timer = setTimeout(async () => {
			if (amount <= 0) {
				flags = [];
				return;
			}
			try {
				const res = await api.regulatoryCheck(payload);
				flags = res.flags;
				cap = res.rate_cap_daily;
				dsr = res.dsr;
			} catch {
				/* abaikan error cek */
			}
		}, 280);
		return () => clearTimeout(timer);
	});

	const levelText: Record<string, string> = {
		red: 'Di atas batas OJK',
		orange: 'Perhatian',
		yellow: 'Catatan'
	};
</script>

{#if flags.length}
	<div class="space-y-2">
		{#each flags as f (f.code)}
			<div
				class="flex items-start gap-3 rounded-xl border p-3 text-sm"
				class:alert-red={f.level === 'red'}
				class:alert-warn={f.level === 'orange'}
				class:alert-line={f.level === 'yellow'}
			>
				<Badge level={f.level}>{levelText[f.level] ?? 'Catatan'}</Badge>
				<p class="flex-1 text-[var(--color-ink-dim)]">{f.msg}</p>
			</div>
		{/each}
	</div>
{:else if amount > 0}
	<div
		class="flex items-center gap-3 rounded-xl border border-[var(--color-ok)] bg-emerald-500/10 p-3 text-sm"
	>
		<Badge level="ok">Sesuai batas</Badge>
		<p class="flex-1 text-[var(--color-ink-dim)]">
			Bunga dan rasio cicilan masih dalam batas OJK ({(cap * 100)
				.toFixed(2)
				.replace('.', ',')}%/hari, DSR {(dsr * 100).toFixed(0)}%).
		</p>
	</div>
{/if}
