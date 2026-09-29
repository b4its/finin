<script lang="ts">
	import type { Twin } from '$lib/api/types';
	import { twinIcon } from '$lib/utils/icons';

	let { twins = [] }: { twins: Twin[] } = $props();

	interface HealthScore {
		twin: Twin;
		overall: number;
		grade: string;
		gradeColor: string;
		liquidity: number;
		debtSafety: number;
		stressResilience: number;
		wealthGrowth: number;
		regulatory: number;
		diagnosis: string;
	}

	let healthScores = $derived<HealthScore[]>(
		twins.map((t) => {
			const minEf = Number(t.summary?.min_emergency_months ?? 0);
			const avgDsr = Number(t.summary?.avg_dsr ?? 0);
			const survivedAll = (t.stress ?? []).every((s) => s.survived);
			const y10Real = t.yearly_series.find((p) => p.year === 10)?.net_worth_real ?? 0;
			const y0Real = t.yearly_series.find((p) => p.year === 0)?.net_worth_real ?? 0;
			const hasRedFlag = t.flags.some((f) => f.level === 'red');
			const hasSlik = t.flags.some((f) => f.code === 'SLIK_DEFAULT');

			// 1. Likuiditas (0-100)
			let liquidity = 20;
			if (minEf >= 6) liquidity = 100;
			else if (minEf >= 3) liquidity = 80;
			else if (minEf >= 1) liquidity = 50;

			// 2. Beban Utang / DSR (0-100)
			let debtSafety = 20;
			if (avgDsr === 0) debtSafety = 100;
			else if (avgDsr <= 0.15) debtSafety = 95;
			else if (avgDsr <= 0.3) debtSafety = 80;
			else if (avgDsr <= 0.4) debtSafety = 40;

			// 3. Stress Test (0-100)
			let stressResilience = 20;
			if (survivedAll) stressResilience = 100;
			else if ((t.stress ?? []).some((s) => s.survived)) stressResilience = 50;

			// 4. Pertumbuhan Riil (0-100)
			let wealthGrowth = 30;
			if (y10Real > y0Real * 2) wealthGrowth = 100;
			else if (y10Real > y0Real) wealthGrowth = 75;
			else if (y10Real >= y0Real * 0.8) wealthGrowth = 50;

			// 5. Regulasi & SLIK OJK (0-100)
			let regulatory = 100;
			if (hasSlik) regulatory = 0;
			else if (hasRedFlag) regulatory = 30;
			else if (t.flags.some((f) => f.level === 'orange')) regulatory = 60;

			const overall = Math.round(
				liquidity * 0.25 +
					debtSafety * 0.25 +
					stressResilience * 0.2 +
					wealthGrowth * 0.2 +
					regulatory * 0.1
			);

			let grade = 'D';
			let gradeColor = 'text-rose-400 border-rose-500 bg-rose-500/10';
			let diagnosis = 'Kondisi finansial rentan guncangan dan berisiko tinggi.';
			if (overall >= 85) {
				grade = 'A';
				gradeColor = 'text-emerald-400 border-emerald-500 bg-emerald-500/10';
				diagnosis = 'Kesehatan finansial prima, likuiditas kuat & tahan krisis.';
			} else if (overall >= 70) {
				grade = 'B';
				gradeColor = 'text-cyan-400 border-cyan-500 bg-cyan-500/10';
				diagnosis = 'Struktur finansial stabil, namun perlu jaga disiplin rasio utang.';
			} else if (overall >= 55) {
				grade = 'C';
				gradeColor = 'text-amber-400 border-amber-500 bg-amber-500/10';
				diagnosis = 'Bantalan kas tipis atau beban cicilan mendekati batas aman OJK.';
			}

			return {
				twin: t,
				overall,
				grade,
				gradeColor,
				liquidity,
				debtSafety,
				stressResilience,
				wealthGrowth,
				regulatory,
				diagnosis
			};
		})
	);
</script>

<div class="card p-4">
	<div class="mb-4 flex items-center justify-between">
		<div>
			<h3 class="flex items-center gap-2 text-sm font-semibold text-[var(--color-ink)]">
				<span>🩺</span> Rapor Kesehatan Finansial 360°
			</h3>
			<p class="text-xs text-[var(--color-ink-dim)]">
				Evaluasi holistik: likuiditas, batas utang OJK, ketahanan krisis, dan pertumbuhan riil
			</p>
		</div>
	</div>

	<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
		{#each healthScores as hs}
			<div
				class="flex flex-col justify-between rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3.5 transition-colors hover:border-[var(--color-accent)]"
			>
				<div>
					<div
						class="flex items-center justify-between border-b border-[var(--color-line)]/50 pb-2.5"
					>
						<div class="flex items-center gap-1.5 font-bold text-xs">
							<span style="color:{hs.twin.color}">{twinIcon(hs.twin.icon)}</span>
							<span>Twin {hs.twin.code}: {hs.twin.label}</span>
						</div>
						<span class="rounded-lg border px-2 py-0.5 text-xs font-black {hs.gradeColor}">
							Grade {hs.grade}
						</span>
					</div>

					<div class="mt-3 flex items-baseline justify-between">
						<span class="text-xs text-[var(--color-ink-dim)] font-medium">Skor Kesehatan:</span>
						<span class="num text-2xl font-extrabold text-[var(--color-ink)]">
							{hs.overall}<span class="text-xs font-normal text-[var(--color-ink-dim)]">/100</span>
						</span>
					</div>

					<!-- Progress bar -->
					<div class="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-void-3)]">
						<div
							class="h-full rounded-full transition-all duration-500"
							style="width: {hs.overall}%; background-color: {hs.twin.color}"
						></div>
					</div>

					<!-- Detail 5 Pilar (termasuk Regulasi OJK yang berbobot 10% di skor) -->
					<div class="mt-3 space-y-1.5 text-[11px]">
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>🛡️ Dana Darurat & Kas</span>
							<span class="num font-semibold text-[var(--color-ink)]">{hs.liquidity}%</span>
						</div>
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>⚖️ Keamanan Utang (DSR)</span>
							<span class="num font-semibold text-[var(--color-ink)]">{hs.debtSafety}%</span>
						</div>
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>⚡ Ketahanan Guncangan</span>
							<span class="num font-semibold text-[var(--color-ink)]">{hs.stressResilience}%</span>
						</div>
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>📈 Akumulasi Riil</span>
							<span class="num font-semibold text-[var(--color-ink)]">{hs.wealthGrowth}%</span>
						</div>
						<div class="flex justify-between text-[var(--color-ink-dim)]">
							<span>🚩 Regulasi & SLIK OJK</span>
							<span class="num font-semibold text-[var(--color-ink)]">{hs.regulatory}%</span>
						</div>
					</div>
				</div>

				<div
					class="mt-3 border-t border-[var(--color-line)]/50 pt-2 text-[10px] leading-relaxed text-[var(--color-ink-dim)]"
				>
					{hs.diagnosis}
				</div>
			</div>
		{/each}
	</div>
</div>
