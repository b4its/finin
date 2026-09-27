<script lang="ts">
	import type { Twin } from '$lib/api/types';
	import { twinIcon } from '$lib/utils/icons';

	let { twins = [] }: { twins: Twin[] } = $props();

	interface MilestoneMeta {
		key: string;
		label: string;
		icon: string;
		desc: string;
	}

	const MILESTONES: MilestoneMeta[] = [
		{
			key: 'emergency_fund_full',
			label: 'Dana Darurat Aman',
			icon: '🛡️',
			desc: 'Memiliki bantalan kas likuid minimal 3–6 bulan pengeluaran'
		},
		{
			key: 'net_worth_100m',
			label: '100 Juta Pertama',
			icon: '🚀',
			desc: 'Tonggak psikologis tersulit akumulasi modal awal'
		},
		{
			key: 'debt_free',
			label: 'Bebas Seluruh Utang',
			icon: '⛓️',
			desc: 'Seluruh saldo pinjaman/cicilan lunas sepenuhnya'
		},
		{
			key: 'net_worth_1b',
			label: '1 Miliar Pertama',
			icon: '🏆',
			desc: 'Mencapai kekayaan nominal 10 digit (Rp 1.000.000.000)'
		},
		{
			key: 'financial_independence',
			label: 'Kemandirian Finansial (FIRE)',
			icon: '🏖️',
			desc: 'Net worth riil melampaui 25× pengeluaran tahunan'
		}
	];

	function formatMonth(m: number | null | undefined): string {
		if (m === undefined || m === null) return 'Belum tercapai';
		if (m === 0) return 'Tercapai di awal (Bln 0)';
		const y = Math.floor(m / 12);
		const rem = m % 12;
		if (y === 0) return `Bulan ke-${rem}`;
		if (rem === 0) return `Tahun ke-${y} (${m} bln)`;
		return `Thn ${y}, Bln ${rem} (${m} bln)`;
	}

	function getFastestTwinCode(key: string): string | null {
		const reached = twins
			.map((t) => ({ code: t.code, month: t.milestones?.[key] }))
			.filter((x): x is { code: string; month: number } => typeof x.month === 'number');

		if (!reached.length) return null;
		reached.sort((a, b) => a.month - b.month);
		return reached[0].code;
	}
</script>

<div class="card p-4">
	<div class="mb-4 flex items-center justify-between">
		<div>
			<h3 class="flex items-center gap-2 text-sm font-semibold text-[var(--color-ink)]">
				<span>🚩</span> Pencapaian Tonggak Finansial
			</h3>
			<p class="text-xs text-[var(--color-ink-dim)]">
				Kecepatan tiap kembar mencapai tonggak hidup penting dalam 20 tahun (240 bulan)
			</p>
		</div>
	</div>

	<div class="space-y-3">
		{#each MILESTONES as ms}
			{@const fastest = getFastestTwinCode(ms.key)}
			<div
				class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3 transition-colors hover:border-[var(--color-accent)]"
			>
				<div
					class="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--color-line)]/50 pb-2"
				>
					<div class="flex items-center gap-2">
						<span class="text-base">{ms.icon}</span>
						<div>
							<span class="font-bold text-xs text-[var(--color-ink)]">{ms.label}</span>
							<span class="ml-2 hidden text-[11px] text-[var(--color-ink-dim)] sm:inline">
								— {ms.desc}
							</span>
						</div>
					</div>
				</div>

				<div class="mt-2.5 grid grid-cols-1 gap-2 sm:grid-cols-3">
					{#each twins as t}
						{@const m = t.milestones?.[ms.key]}
						{@const isFastest = fastest !== null && t.code === fastest && m !== null}
						<div
							class="flex items-center justify-between rounded-lg border p-2 text-xs transition-all {isFastest
								? 'border-emerald-500/60 bg-emerald-500/10'
								: 'border-[var(--color-line)] bg-[var(--color-void-1)]'}"
						>
							<div class="flex items-center gap-1.5 font-medium">
								<span style="color: {t.color}">{twinIcon(t.icon)}</span>
								<span class="font-bold text-[11px]">Twin {t.code}:</span>
							</div>

							<div class="flex items-center gap-1">
								<span
									class="num text-[11px] font-semibold {m !== null && m !== undefined
										? isFastest
											? 'text-emerald-400 font-bold'
											: 'text-[var(--color-ink)]'
										: 'text-[var(--color-ink-dim)] opacity-50'}"
								>
									{formatMonth(m)}
								</span>
								{#if isFastest && m !== 0}
									<span class="text-[10px]" title="Tercepat mencapai tonggak ini">🥇</span>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/each}
	</div>
</div>
