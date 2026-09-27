<script lang="ts">
	import type { Simulation, Recommendation, Twin } from '$lib/api/types';
	import { rupiah, rupiahBrief, percent, months } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';

	let {
		open = $bindable(false),
		simulation,
		recommendation
	}: {
		open: boolean;
		simulation: Simulation;
		recommendation: Recommendation | null;
	} = $props();

	let bestTwin = $derived(
		simulation.twins.find((t) => t.code === (recommendation?.best_twin ?? simulation.best_twin))
	);

	function printReport() {
		window.print();
	}
</script>

{#if open}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/80 p-4 print:static print:bg-white print:p-0"
		role="dialog"
		aria-modal="true"
	>
		<div
			class="relative my-8 w-full max-w-4xl rounded-2xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-6 shadow-2xl print:my-0 print:border-none print:bg-white print:p-0 print:text-black print:shadow-none"
		>
			<!-- Bar Aksi (Hanya layar, disembunyikan saat cetak) -->
			<div
				class="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4 print:hidden"
			>
				<div class="flex items-center gap-2">
					<span class="text-xl">📄</span>
					<div>
						<h2 class="text-base font-bold text-[var(--color-ink)]">
							Laporan Eksekutif Financial Twin
						</h2>
						<p class="text-xs text-[var(--color-ink-dim)]">
							Siap dicetak atau disimpan sebagai berkas PDF
						</p>
					</div>
				</div>
				<div class="flex items-center gap-2">
					<button class="btn btn-primary !py-2 text-xs" onclick={printReport}>
						🖨️ Cetak / Simpan PDF
					</button>
					<button class="btn btn-ghost !py-2 text-xs" onclick={() => (open = false)}>
						✕ Tutup
					</button>
				</div>
			</div>

			<!-- Lembar Laporan Cetak -->
			<div class="space-y-6 text-[var(--color-ink)] print:text-black">
				<!-- Header Dokumen -->
				<div
					class="flex items-start justify-between border-b border-[var(--color-line)] pb-5 print:border-black/20"
				>
					<div>
						<div class="flex items-center gap-2">
							<span class="text-2xl print:hidden">🌌</span>
							<h1 class="text-xl font-extrabold tracking-tight">FINANCIAL TWIN</h1>
						</div>
						<p class="mt-0.5 text-xs text-[var(--color-ink-dim)] print:text-gray-600">
							Decision Support System · Multi-Scenario Long-Term Projection (5, 10, 20 Tahun)
						</p>
					</div>
					<div class="text-right text-xs">
						<div class="font-mono text-[var(--color-ink-dim)] print:text-gray-600">
							ID: {simulation.id.slice(0, 13)}...
						</div>
						<div class="mt-0.5 font-medium">
							Asumsi: {simulation.assumption_code} ({simulation.assumption_as_of})
						</div>
						<div class="text-[10px] text-[var(--color-ink-dim)] print:text-gray-600">
							Engine v{simulation.engine_version} · Regulasi OJK 2025/2026
						</div>
					</div>
				</div>

				<!-- Bagian Rekomendasi Terpilih -->
				{#if recommendation && bestTwin}
					<div
						class="rounded-xl border border-[var(--color-accent)] bg-blue-500/5 p-4 print:border-black print:bg-gray-50"
					>
						<div class="flex items-center justify-between">
							<span
								class="text-xs font-bold uppercase tracking-wider text-[var(--color-accent)] print:text-black"
							>
								Rekomendasi Utama Deterministik
							</span>
							<span
								class="rounded-full px-2 py-0.5 text-xs font-bold"
								style="background:{bestTwin.color}; color:#000;"
							>
								Twin {bestTwin.code}: {bestTwin.label} (Skor {(bestTwin.score * 100).toFixed(
									0
								)}/100)
							</span>
						</div>

						<div class="mt-3">
							<div class="text-xs font-semibold text-[var(--color-ink-dim)] print:text-gray-700">
								LANGKAH PERTAMA HARI INI:
							</div>
							<p class="mt-0.5 text-sm font-bold leading-relaxed">{recommendation.first_step}</p>
						</div>

						<div
							class="mt-2 text-xs leading-relaxed text-[var(--color-ink-dim)] print:text-gray-700"
						>
							<span class="font-semibold">Dasar pertimbangan:</span>
							{recommendation.rationale}
						</div>

						<div class="mt-2 text-[11px] text-[var(--color-ink-dim)] print:text-gray-600">
							<span class="font-medium">Ketahanan Asumsi:</span>
							{simulation.robust
								? '✓ Rekomendasi Robust (konsisten di preset Konservatif, Moderat, dan Optimis).'
								: `Sensitif terhadap asumsi (${simulation.robust_reason || 'bergantung skenario market'}).`}
						</div>
					</div>
				{/if}

				<!-- Matriks Perbandingan Seluruh Twin -->
				<div>
					<h3
						class="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--color-ink-dim)] print:text-gray-700"
					>
						Matriks Proyeksi Multi-Twin (Horizon 5, 10, 20 Tahun)
					</h3>
					<div class="overflow-x-auto">
						<table
							class="w-full text-left text-xs border-collapse print:border print:border-black/20"
						>
							<thead>
								<tr
									class="border-b border-[var(--color-line)] bg-[var(--color-void-2)] print:bg-gray-100 print:border-black/20"
								>
									<th class="p-2 font-semibold">Twin</th>
									<th class="p-2 font-semibold">Net Worth Riil (Th 5)</th>
									<th class="p-2 font-semibold">Net Worth Riil (Th 10)</th>
									<th class="p-2 font-semibold">Net Worth Riil (Th 20)</th>
									<th class="p-2 font-semibold">Dana Darurat Min</th>
									<th class="p-2 font-semibold">DSR Rata-rata</th>
									<th class="p-2 font-semibold">Status OJK / SLIK</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-[var(--color-line)] print:divide-black/10">
								{#each simulation.twins as t}
									{@const s5 = t.yearly_series.find((p) => p.year === 5)}
									{@const s10 = t.yearly_series.find((p) => p.year === 10)}
									{@const s20 = t.yearly_series.find((p) => p.year === 20)}
									{@const isBest = t.code === bestTwin?.code}
									<tr class={isBest ? 'bg-blue-500/5 font-semibold print:bg-gray-50' : ''}>
										<td class="p-2">
											<span class="inline-block w-4 font-bold" style="color:{t.color}"
												>{twinIcon(t.icon)}</span
											>
											<span>Twin {t.code}: {t.label}</span>
											{#if isBest}<span
													class="ml-1 text-[10px] text-[var(--color-accent)] font-bold"
													>★ Rekomendasi</span
												>{/if}
										</td>
										<td class="p-2 num">{s5 ? rupiahBrief(s5.net_worth_real) : '—'}</td>
										<td class="p-2 num">{s10 ? rupiahBrief(s10.net_worth_real) : '—'}</td>
										<td class="p-2 num">{s20 ? rupiahBrief(s20.net_worth_real) : '—'}</td>
										<td class="p-2 num">{months(Number(t.summary?.min_emergency_months ?? 0))}</td>
										<td class="p-2 num">{percent(Number(t.summary?.avg_dsr ?? 0))}</td>
										<td class="p-2 text-[10px]">
											{#if t.flags.some((f) => f.level === 'red')}
												<span class="text-rose-400 font-semibold print:text-red-700"
													>Di Atas Batas OJK</span
												>
											{:else if t.flags.some((f) => f.code === 'SLIK_DEFAULT')}
												<span class="text-amber-400 font-semibold print:text-amber-700"
													>Macet (SLIK OJK)</span
												>
											{:else if t.flags.some((f) => f.level === 'orange')}
												<span class="text-amber-400 print:text-amber-700">DSR &gt; 30%</span>
											{:else}
												<span class="text-emerald-400 print:text-green-700">Patuh OJK</span>
											{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>

				<!-- Hasil Uji Ketahanan (Stress Test) -->
				<div>
					<h3
						class="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--color-ink-dim)] print:text-gray-700"
					>
						Uji Ketahanan Finansial (Stress Test Guncangan)
					</h3>
					<div class="grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs">
						{#each simulation.twins[0]?.stress ?? [] as shock}
							<div class="rounded-lg border border-[var(--color-line)] p-3 print:border-black/20">
								<div class="font-bold">{shock.label}</div>
								<div
									class="mt-1 space-y-1 text-[11px] text-[var(--color-ink-dim)] print:text-gray-600"
								>
									{#each simulation.twins as t}
										{@const ts = t.stress.find((s) => s.shock === shock.shock)}
										<div class="flex justify-between items-center">
											<span>Twin {t.code} ({t.label}):</span>
											<span
												class={ts?.survived
													? 'text-emerald-400 font-semibold print:text-green-700'
													: 'text-rose-400 font-semibold print:text-red-700'}
											>
												{ts?.survived ? '✓ Bertahan' : '✗ Tidak Bertahan'}
											</span>
										</div>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				</div>

				<!-- Transparansi Regulasi & Sumber Asumsi -->
				<div
					class="border-t border-[var(--color-line)] pt-4 text-[11px] text-[var(--color-ink-dim)] print:border-black/20 print:text-gray-600"
				>
					<div class="font-bold text-[var(--color-ink)] print:text-black">
						Kepatuhan Regulasi & Sumber Parameter:
					</div>
					<p class="mt-1 leading-relaxed">
						Aturan pinjaman mengacu pada <strong>SEOJK 19/SEOJK.06/2025</strong> (batas bunga harian 0,3%
						tenor ≤6 bulan; 0,2% tenor &gt;6 bulan; lock cap 100% pokok pinjaman; batas DSR 30% penghasilan).
						Asumsi makroekonomi: inflasi dasar 3,0%/th (sasaran BI PMK 31/2024), bunga penjaminan LPS
						bank umum 3,75% (periode berlaku September 2026), SBN ritel 6,8% (SR025 Kemenkeu).
					</p>
					<div
						class="mt-3 rounded-lg border border-[var(--color-line)] p-3 italic text-[10px] print:border-black/20"
					>
						<strong>Disclaimer Resmi:</strong> Financial Twin adalah alat simulasi edukatif, bukan nasihat
						keuangan, investasi, atau hukum. Proyeksi bergantung pada asumsi dan tidak menjamin hasil
						masa depan. Konsultasikan keputusan finansial penting dengan perencana keuangan berlisensi.
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	@media print {
		:global(body) {
			background: white !important;
			color: black !important;
		}
	}
</style>
