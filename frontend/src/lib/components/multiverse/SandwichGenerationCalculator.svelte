<script lang="ts">
	import type { Profile, Twin } from '$lib/api/types';
	import { rupiah, rupiahBrief, percent } from '$lib/utils/format';

	let { profile, twins = [] }: { profile?: Profile; twins?: Twin[] } = $props();

	// Parameter Beban Tanggungan Generasi Sandwich
	let parentAllowanceMonthly = $state(1_500_000); // Uang saku/kebutuhan orang tua
	let parentHealthMonthly = $state(500_000); // Obat kronis lansia & BPJS mandiri
	let childCount = $state(1); // Jumlah anak
	let childEducationMonthly = $state(1_200_000); // SPP & les per anak/bulan

	let incomeMonthly = $derived(profile?.income_monthly ?? 12_000_000);

	// Total beban
	let totalParentBurden = $derived(parentAllowanceMonthly + parentHealthMonthly);
	let totalChildBurden = $derived(childCount * childEducationMonthly);
	let totalSandwichBurden = $derived(totalParentBurden + totalChildBurden);

	// Dependency Burden Ratio (Rasio Beban Tanggungan terhadap Penghasilan Kotor)
	let dependencyRatio = $derived(incomeMonthly > 0 ? totalSandwichBurden / incomeMonthly : 0);

	// Estimasi akumulasi 10 & 20 tahun
	let cumulative10y = $derived(totalSandwichBurden * 12 * 10);
	let cumulative20y = $derived(totalSandwichBurden * 12 * 20);

	// Estimasi penundaan FIRE / Dana Mandiri
	// Rata-rata 10% rasio tanggungan menunda usia pensiun mandiri ~1.8 tahun
	let fireDelayYears = $derived(Math.min(15, Math.round(dependencyRatio * 18)));

	// Status ketahanan finansial
	let statusInfo = $derived.by(() => {
		if (dependencyRatio <= 0.2) {
			return {
				grade: 'Aman (Terkendali)',
				color: 'text-emerald-400',
				bg: 'bg-emerald-500/10 border-emerald-500/30',
				badge: 'bg-emerald-500/15 text-emerald-400',
				desc: 'Beban tanggungan keluarga di bawah 20% pendapatan. Anda masih memiliki fleksibilitas tinggi untuk berinvestasi dan menabung dana darurat.'
			};
		}
		if (dependencyRatio <= 0.35) {
			return {
				grade: 'Waspada (Beban Menengah)',
				color: 'text-amber-400',
				bg: 'bg-amber-500/10 border-amber-500/30',
				badge: 'bg-amber-500/15 text-amber-400',
				desc: 'Beban tanggungan menyerap 20–35% penghasilan. Prioritaskan kepesertaan BPJS Kesehatan orang tua agar guncangan medis darurat tidak membobol tabungan.'
			};
		}
		return {
			grade: 'Kritis (Sandwich Trap)',
			color: 'text-rose-400',
			bg: 'bg-rose-500/10 border-rose-500/30',
			badge: 'bg-rose-500/15 text-rose-400',
			desc: 'Lebih dari 35% penghasilan habis menopang dua generasi sekaligus. Sangat rentan terhadap risiko gagal bayar bila pencari nafkah sakit atau kehilangan pekerjaan.'
		};
	});
</script>

<div class="card p-5">
	<div class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4">
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">🥪</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Kalkulator Ketahanan Finansial Generasi Sandwich
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Simulasi dampak tanggungan ganda (orang tua pensiun + anak) terhadap arus kas, dana darurat, dan target kemerdekaan finansial.
			</p>
		</div>

		<span class="rounded-full px-2.5 py-1 text-xs font-bold {statusInfo.badge}">
			{statusInfo.grade} ({percent(dependencyRatio, 1)})
		</span>
	</div>

	<!-- Kontrol Parameter Beban Tanggungan -->
	<div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
		<div class="space-y-1.5">
			<span class="block text-xs font-medium text-[var(--color-ink-dim)]">Nafkah Orang Tua/Bulan</span>
			<div class="flex items-center gap-1 rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] px-2.5 py-1.5">
				<span class="text-xs text-[var(--color-ink-dim)]">Rp</span>
				<input
					type="number"
					class="w-full bg-transparent font-mono text-xs font-bold text-[var(--color-ink)] focus:outline-none"
					bind:value={parentAllowanceMonthly}
					step="100000"
				/>
			</div>
			<span class="text-[10px] text-[var(--color-ink-dim)]">Uang saku, pangan, belanja harian lansia</span>
		</div>

		<div class="space-y-1.5">
			<span class="block text-xs font-medium text-[var(--color-ink-dim)]">Kesehatan & Obat Lansia/Bulan</span>
			<div class="flex items-center gap-1 rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] px-2.5 py-1.5">
				<span class="text-xs text-[var(--color-ink-dim)]">Rp</span>
				<input
					type="number"
					class="w-full bg-transparent font-mono text-xs font-bold text-[var(--color-ink)] focus:outline-none"
					bind:value={parentHealthMonthly}
					step="50000"
				/>
			</div>
			<span class="text-[10px] text-[var(--color-ink-dim)]">BPJS mandiri orang tua + obat rutin</span>
		</div>

		<div class="space-y-1.5">
			<span class="block text-xs font-medium text-[var(--color-ink-dim)]">Jumlah Anak Tanggungan</span>
			<div class="flex items-center gap-2 rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] px-2.5 py-1.5">
				<input
					type="number"
					class="w-full bg-transparent font-mono text-xs font-bold text-[var(--color-ink)] focus:outline-none"
					bind:value={childCount}
					min="0"
					max="6"
				/>
				<span class="text-xs text-[var(--color-ink-dim)]">Anak</span>
			</div>
			<span class="text-[10px] text-[var(--color-ink-dim)]">Anak belum mandiri finansial</span>
		</div>

		<div class="space-y-1.5">
			<span class="block text-xs font-medium text-[var(--color-ink-dim)]">Biaya Pendidikan/Anak/Bulan</span>
			<div class="flex items-center gap-1 rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] px-2.5 py-1.5">
				<span class="text-xs text-[var(--color-ink-dim)]">Rp</span>
				<input
					type="number"
					class="w-full bg-transparent font-mono text-xs font-bold text-[var(--color-ink)] focus:outline-none"
					bind:value={childEducationMonthly}
					step="100000"
				/>
			</div>
			<span class="text-[10px] text-[var(--color-ink-dim)]">SPP sekolah, les, susu & nutrisi</span>
		</div>
	</div>

	<!-- Dashboard Metrik & Indikator Ketahanan -->
	<div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
			<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Total Beban Tanggungan Bulanan</span>
			<div class="mt-1 text-lg font-bold text-[var(--color-ink)]">{rupiah(totalSandwichBurden)}</div>
			<div class="mt-1 flex items-center justify-between text-[11px] text-[var(--color-ink-dim)]">
				<span>Orang Tua: {rupiahBrief(totalParentBurden)}</span>
				<span>Anak: {rupiahBrief(totalChildBurden)}</span>
			</div>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
			<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Rasio Beban (Dependency Ratio)</span>
			<div class="mt-1 text-lg font-bold {statusInfo.color}">{percent(dependencyRatio, 1)}</div>
			<div class="mt-1 text-[11px] text-[var(--color-ink-dim)]">
				Batas aman perencana keuangan: &lt; 20%
			</div>
		</div>

		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-3.5">
			<span class="text-xs font-semibold text-[var(--color-ink-dim)]">Dampak Terhadap Target FIRE</span>
			<div class="mt-1 text-lg font-bold text-amber-400">+{fireDelayYears} Tahun</div>
			<div class="mt-1 text-[11px] text-[var(--color-ink-dim)]">
				Potensi penundaan usia kemerdekaan finansial
			</div>
		</div>
	</div>

	<!-- Evaluasi Diagnosis & Peringatan Risiko -->
	<div class="mt-4 rounded-xl border p-4 {statusInfo.bg}">
		<div class="flex items-start gap-3">
			<span class="text-xl">⚠️</span>
			<div>
				<h4 class="text-xs font-bold text-[var(--color-ink)]">Diagnosis Ketahanan Arus Kas:</h4>
				<p class="mt-1 text-xs leading-relaxed text-[var(--color-ink-dim)]">{statusInfo.desc}</p>
				<p class="mt-2 text-[11px] text-[var(--color-ink-dim)]">
					Proyeksi kumulatif arus kas untuk tanggungan sandwich: <strong class="text-[var(--color-ink)]">{rupiahBrief(cumulative10y)}</strong> (10 tahun) dan <strong class="text-[var(--color-ink)]">{rupiahBrief(cumulative20y)}</strong> (20 tahun).
				</p>
			</div>
		</div>
	</div>

	<!-- Roadmap Pemutus Rantai Generasi Sandwich (Break the Chain) -->
	<div class="mt-4 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4">
		<h4 class="text-xs font-bold text-[var(--color-ink)]">
			🛡️ Strategi 3 Langkah Memutus Rantai Generasi Sandwich (Break The Chain)
		</h4>
		<div class="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs">
			<div class="rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] p-3 space-y-1">
				<div class="font-bold text-teal-400">1. Proteksi Medis Orang Tua</div>
				<p class="text-[11px] leading-relaxed text-[var(--color-ink-dim)]">
					Daftarkan orang tua pada <strong>BPJS Kesehatan Mandiri (Kelas 1 atau 2)</strong> secara konsisten. Guncangan biaya opname rumah sakit adalah penyebab #1 kebangkrutan sandwich generation.
				</p>
			</div>

			<div class="rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] p-3 space-y-1">
				<div class="font-bold text-blue-400">2. Asuransi Jiwa Murni Anda</div>
				<p class="text-[11px] leading-relaxed text-[var(--color-ink-dim)]">
					Sebagai tulang punggung dua generasi, miliki <strong>Asuransi Jiwa Murni (Term Life)</strong> dengan uang pertanggungan minimal 10x pengeluaran tahunan tanpa embel-embel investasi.
				</p>
			</div>

			<div class="rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] p-3 space-y-1">
				<div class="font-bold text-emerald-400">3. Siapkan Pensiun Mandiri</div>
				<p class="text-[11px] leading-relaxed text-[var(--color-ink-dim)]">
					Akumulasi dana pensiun (BPJS TK JHT + SBN/Saham Dividen) agar kelak ketika Anda berusia 56+ tahun, <strong>anak Anda tidak menjadi sandwich generation jilid berikutnya</strong>.
				</p>
			</div>
		</div>
	</div>
</div>
