<script lang="ts">
	import type { Twin, Profile } from '$lib/api/types';
	import { rupiah, rupiahBrief } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	interface Props {
		twins: Twin[];
		profile?: Profile;
	}

	let { twins }: Props = $props();

	interface GoalPreset {
		id: string;
		label: string;
		sub: string;
		defaultTarget: number;
		icon: string;
		category: 'property' | 'family' | 'business' | 'lifestyle';
	}

	const GOAL_PRESETS: GoalPreset[] = [
		{
			id: 'dp_kpr',
			label: 'DP Rumah Pertama (KPR)',
			sub: 'Down payment 15% + biaya provisi/notaris',
			defaultTarget: 120_000_000,
			icon: '🏠',
			category: 'property'
		},
		{
			id: 'rumah_cash',
			label: 'Beli Rumah Tunai',
			sub: 'Beli rumah bebas beban bunga KPR',
			defaultTarget: 600_000_000,
			icon: '🏡',
			category: 'property'
		},
		{
			id: 'modal_usaha',
			label: 'Modal Rintis Bisnis Mandiri',
			sub: 'Sewa ruko, modal kerja, & cadangan kas 6 bln',
			defaultTarget: 180_000_000,
			icon: '🏪',
			category: 'business'
		},
		{
			id: 'umrah_keluarga',
			label: 'Ibadah Umrah / Haji Khusus',
			sub: 'Biaya paket umrah 2 orang + uang saku',
			defaultTarget: 75_000_000,
			icon: '🕋',
			category: 'family'
		},
		{
			id: 'pernikahan',
			label: 'Modal Rumah Tangga & Nikah',
			sub: 'Resepsi intim + perlengkapan hunian awal',
			defaultTarget: 100_000_000,
			icon: '💍',
			category: 'family'
		},
		{
			id: 'mobil_keluarga',
			label: 'Kendaraan Keluarga Tunai',
			sub: 'Mobil operasional keluarga bebas leasing',
			defaultTarget: 220_000_000,
			icon: '🚗',
			category: 'lifestyle'
		},
		{
			id: 'fire_mini',
			label: 'Mini Financial Freedom',
			sub: 'Bantalan pasif income Rp5 jt/bln (SBN 6%)',
			defaultTarget: 1_000_000_000,
			icon: '🏖️',
			category: 'lifestyle'
		}
	];

	let selectedGoalId = $state<string>('dp_kpr');
	let customTarget = $state<number>(120_000_000);
	let useRealValue = $state<boolean>(false); // Menggunakan nilai riil (disesuaikan inflasi) atau nominal

	function selectGoal(preset: GoalPreset) {
		selectedGoalId = preset.id;
		customTarget = preset.defaultTarget;
	}

	interface TwinGoalAchievement {
		twin: Twin;
		achievedYear: number | null;
		achievedNetWorth: number;
		currentYear10NetWorth: number;
		progressPct: number;
		statusLabel: string;
		statusColor: 'emerald' | 'amber' | 'indigo' | 'rose';
	}

	// Hitung tahun pencapaian tiap Twin
	let twinAchievements = $derived.by<TwinGoalAchievement[]>(() => {
		const target = Math.max(1_000_000, customTarget);

		return twins.map((t) => {
			let achievedYear: number | null = null;
			let achievedNetWorth = 0;

			for (const pt of t.yearly_series) {
				const val = useRealValue ? pt.net_worth_real : pt.net_worth;
				if (val >= target) {
					achievedYear = pt.year;
					achievedNetWorth = val;
					break;
				}
			}

			// Ambil nilai tahun ke-10 (atau tahun terakhir jika horizon < 10)
			const pt10 =
				t.yearly_series.find((p) => p.year === 10) ?? t.yearly_series[t.yearly_series.length - 1];
			const nw10 = pt10 ? (useRealValue ? pt10.net_worth_real : pt10.net_worth) : 0;
			const progressPct = Math.min(100, Math.max(0, (nw10 / target) * 100));

			let statusLabel = 'Belum tercapai dalam 20 th';
			let statusColor: 'emerald' | 'amber' | 'indigo' | 'rose' = 'rose';

			if (achievedYear !== null) {
				if (achievedYear <= 3) {
					statusLabel = `Tercapai Kilat (Th-${achievedYear})`;
					statusColor = 'emerald';
				} else if (achievedYear <= 7) {
					statusLabel = `Tercapai Cepat (Th-${achievedYear})`;
					statusColor = 'indigo';
				} else if (achievedYear <= 12) {
					statusLabel = `Tercapai Moderat (Th-${achievedYear})`;
					statusColor = 'amber';
				} else {
					statusLabel = `Tercapai Lambat (Th-${achievedYear})`;
					statusColor = 'amber';
				}
			}

			return {
				twin: t,
				achievedYear,
				achievedNetWorth,
				currentYear10NetWorth: nw10,
				progressPct,
				statusLabel,
				statusColor
			};
		});
	});

	// Temukan kembaran tercepat yang mencapai target
	let fastestTwin = $derived.by(() => {
		const achieved = twinAchievements.filter((a) => a.achievedYear !== null);
		if (!achieved.length) return null;
		return achieved.reduce((prev, curr) =>
			(curr.achievedYear ?? 99) < (prev.achievedYear ?? 99) ? curr : prev
		);
	});

	// Bandingkan selisih waktu tercepat vs terlama
	let timeGapAnalysis = $derived.by(() => {
		if (!fastestTwin || fastestTwin.achievedYear === null) return null;
		const others = twinAchievements.filter(
			(a) => a.twin.code !== fastestTwin?.twin.code && a.achievedYear !== null
		);
		if (!others.length) return null;
		const slowest = others.reduce((prev, curr) =>
			(curr.achievedYear ?? 0) > (prev.achievedYear ?? 0) ? curr : prev
		);
		if (slowest.achievedYear === null) return null;
		const gapYears = slowest.achievedYear - fastestTwin.achievedYear;
		if (gapYears <= 0) return null;

		return {
			fastestLabel: fastestTwin.twin.label,
			fastestYear: fastestTwin.achievedYear,
			slowestLabel: slowest.twin.label,
			slowestYear: slowest.achievedYear,
			gapYears
		};
	});
</script>

<div class="card space-y-5 p-5">
	<div
		class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4"
	>
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🎯</span>
				<h3 class="font-bold">Timeline Target Impian & Kebebasan Finansial</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Lihat di tahun ke berapa setiap kembaran digitalmu mampu merealisasikan target finansial
				besarmu.
			</p>
		</div>
		<div class="flex items-center gap-2">
			<button
				type="button"
				class="chip text-xs {useRealValue
					? 'border-[var(--color-accent)] text-[var(--color-accent)] font-semibold'
					: 'text-[var(--color-ink-dim)]'}"
				onclick={() => (useRealValue = !useRealValue)}
				title="Sesuaikan nilai target dengan daya beli riil terhadap inflasi"
			>
				{useRealValue ? '💎 Nilai Riil (Bebas Inflasi)' : '🏷️ Nilai Nominal'}
			</button>
		</div>
	</div>

	<!-- Pemilihan Preset Target Finansial -->
	<div>
		<span class="mb-2 block text-xs font-semibold text-[var(--color-ink)]">
			Pilih Sasaran Target Finansial
		</span>
		<div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
			{#each GOAL_PRESETS as p}
				<button
					type="button"
					class="flex flex-col items-start rounded-xl border p-2.5 text-left transition {selectedGoalId ===
					p.id
						? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-[var(--color-ink)]'
						: 'border-[var(--color-line)] bg-[var(--color-void-2)] hover:border-slate-600'}"
					onclick={() => selectGoal(p)}
				>
					<div class="flex items-center gap-1.5 font-semibold text-xs">
						<span>{p.icon}</span>
						<span class="truncate">{p.label}</span>
					</div>
					<span class="mt-1 text-[10px] text-[var(--color-ink-dim)] truncate w-full">{p.sub}</span>
					<span class="mt-1.5 font-mono text-xs font-bold text-[var(--color-accent)]">
						{rupiahBrief(p.defaultTarget)}
					</span>
				</button>
			{/each}
		</div>
	</div>

	<!-- Input Custom Target Nominal -->
	<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3.5">
		<div class="flex flex-wrap items-center justify-between gap-3">
			<div class="flex-1 min-w-[200px]">
				<label
					for="custom-goal-target"
					class="block text-[11px] font-medium text-[var(--color-ink-dim)]"
				>
					Nominal Target Sasaran (bisa disesuaikan):
				</label>
				<input
					id="custom-goal-target"
					type="number"
					step="10000000"
					min="10000000"
					max="10000000000"
					bind:value={customTarget}
					class="mt-1.5 w-full rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] px-3 py-1.5 font-mono text-sm text-[var(--color-ink)]"
				/>
			</div>
			<div class="text-right">
				<span class="block text-[11px] text-[var(--color-ink-dim)]">Target Terpilih</span>
				<span class="font-mono text-xl font-black text-[var(--color-accent)]">
					{rupiah(customTarget)}
				</span>
			</div>
		</div>
	</div>

	<!-- Highlight Opportunity Cost / Speedup Gap -->
	{#if timeGapAnalysis}
		<div class="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4">
			<div class="flex items-center gap-2">
				<span class="text-base">⚡</span>
				<h4 class="text-xs font-bold text-indigo-300">Akselerasi Pencapaian Antar Keputusan</h4>
			</div>
			<p class="mt-1.5 text-xs text-[var(--color-ink)]">
				<strong>{timeGapAnalysis.fastestLabel}</strong> mencapai target {rupiahBrief(customTarget)}
				di
				<span class="font-mono font-bold text-emerald-400"
					>Tahun ke-{timeGapAnalysis.fastestYear}</span
				>, unggul
				<strong class="text-indigo-300 font-bold"
					>{timeGapAnalysis.gapYears} tahun lebih cepat</strong
				>
				dibandingkan {timeGapAnalysis.slowestLabel} (Tahun ke-{timeGapAnalysis.slowestYear}).
			</p>
			<p class="mt-1 text-[11px] text-[var(--color-ink-dim)]">
				💡 Keputusan finansial hari ini secara nyata memajukan atau menunda impian hidupmu hingga
				bertahun-tahun.
			</p>
		</div>
	{/if}

	<!-- Garis Waktu & Race Track Antarkembar -->
	<div class="space-y-3">
		<h4 class="text-xs font-semibold text-[var(--color-ink)]">
			Race Track Pencapaian Target Antarkembar (Horizon 20 Tahun)
		</h4>
		<div class="space-y-2.5">
			{#each twinAchievements as ta (ta.twin.code)}
				<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3.5">
					<div class="flex flex-wrap items-center justify-between gap-2">
						<div class="flex items-center gap-2">
							<span
								class="inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold"
								style="background: {ta.twin.color}20; color: {ta.twin.color};"
							>
								{twinIcon(ta.twin.icon)}
							</span>
							<div>
								<span class="font-bold text-xs">{ta.twin.label}</span>
								<span class="ml-1 text-[11px] text-[var(--color-ink-dim)]">({ta.twin.code})</span>
							</div>
						</div>

						<div class="flex items-center gap-2">
							<span
								class="rounded-full px-2.5 py-0.5 text-[10px] font-bold border"
								class:border-emerald-500-30={ta.statusColor === 'emerald'}
								class:bg-emerald-500-20={ta.statusColor === 'emerald'}
								class:text-emerald-400={ta.statusColor === 'emerald'}
								class:border-indigo-500-30={ta.statusColor === 'indigo'}
								class:bg-indigo-500-20={ta.statusColor === 'indigo'}
								class:text-indigo-400={ta.statusColor === 'indigo'}
								class:border-amber-500-30={ta.statusColor === 'amber'}
								class:bg-amber-500-20={ta.statusColor === 'amber'}
								class:text-amber-400={ta.statusColor === 'amber'}
								class:border-rose-500-30={ta.statusColor === 'rose'}
								class:bg-rose-500-20={ta.statusColor === 'rose'}
								class:text-rose-400={ta.statusColor === 'rose'}
							>
								{ta.statusLabel}
							</span>
							<span class="font-mono text-xs font-bold text-[var(--color-ink)]">
								{ta.progressPct.toFixed(0)}% (th-10)
							</span>
						</div>
					</div>

					<!-- Visual 20-Year Timeline Track -->
					<div
						class="relative mt-3 h-3.5 w-full rounded-full bg-[var(--color-void-3)] overflow-hidden"
					>
						<!-- Milestone tick marks (Year 5, 10, 15) -->
						<div
							class="absolute top-0 bottom-0 w-px bg-slate-600/40"
							style="left: 25%;"
							title="Tahun 5"
						></div>
						<div
							class="absolute top-0 bottom-0 w-px bg-slate-600/40"
							style="left: 50%;"
							title="Tahun 10"
						></div>
						<div
							class="absolute top-0 bottom-0 w-px bg-slate-600/40"
							style="left: 75%;"
							title="Tahun 15"
						></div>

						{#if ta.achievedYear !== null}
							<!-- Progress bar up to achievement year -->
							<div
								class="h-full rounded-full transition-all duration-500"
								style="width: {(ta.achievedYear / 20) * 100}%; background: {ta.twin.color};"
							></div>
							<!-- Flag pin at achievement year -->
							<div
								class="absolute top-0 bottom-0 w-2 rounded-full shadow-lg"
								style="left: calc({(ta.achievedYear / 20) * 100}% - 4px); background: #FFFFFF;"
								title="Tercapai di Tahun ke-{ta.achievedYear}"
							></div>
						{:else}
							<div
								class="h-full rounded-full opacity-40 transition-all duration-500"
								style="width: {Math.min(100, Math.max(0, ta.progressPct))}%; background: #64748B;"
							></div>
						{/if}
					</div>

					<div
						class="mt-2 flex items-center justify-between text-[11px] text-[var(--color-ink-dim)]"
					>
						<span class="text-[10px]">Tahun 1</span>
						<span class="text-[10px]">Tahun 5</span>
						<span class="text-[10px]">Tahun 10</span>
						<span class="text-[10px]">Tahun 15</span>
						<span class="text-[10px]">Tahun 20</span>
					</div>
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	.border-emerald-500-30 {
		border-color: rgba(16, 185, 129, 0.3);
	}
	.bg-emerald-500-20 {
		background-color: rgba(16, 185, 129, 0.2);
	}
	.border-indigo-500-30 {
		border-color: rgba(99, 102, 241, 0.3);
	}
	.bg-indigo-500-20 {
		background-color: rgba(99, 102, 241, 0.2);
	}
	.border-amber-500-30 {
		border-color: rgba(245, 158, 11, 0.3);
	}
	.bg-amber-500-20 {
		background-color: rgba(245, 158, 11, 0.2);
	}
	.border-rose-500-30 {
		border-color: rgba(244, 63, 94, 0.3);
	}
	.bg-rose-500-20 {
		background-color: rgba(244, 63, 94, 0.2);
	}
</style>
