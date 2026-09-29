<script lang="ts">
	import type { Twin, Profile } from '$lib/api/types';
	import { rupiah, rupiahBrief, percent } from '$lib/utils/format';

	let { twins = [], profile }: { twins?: Twin[]; profile?: Profile } = $props();

	type LawRegime = 'khi' | 'kuhperdata';
	let regime = $state<LawRegime>('khi');

	let selectedTwinCode = $state<string>('0');
	let year = $state<number>(10);

	// Ahli Waris Parameters
	let hasSpouse = $state(true);
	let spouseGender = $state<'wife' | 'husband'>('wife'); // Pewaris laki-laki -> istri mewarisi
	let sonsCount = $state(1);
	let daughtersCount = $state(1);
	let hasLivingFather = $state(true);
	let hasLivingMother = $state(true);

	// Twin terpilih
	let currentTwin = $derived(twins.find((t) => t.code === selectedTwinCode) ?? twins[0]);
	let currentNetWorth = $derived.by(() => {
		if (!currentTwin) return 1_000_000_000;
		const pt =
			currentTwin.yearly_series.find((p) => p.year === year) ??
			currentTwin.yearly_series[currentTwin.yearly_series.length - 1];
		return Math.max(0, pt?.net_worth_real ?? pt?.net_worth ?? 1_000_000_000);
	});

	// Perhitungan Pembagian Waris
	interface HeirShare {
		role: string;
		count: number;
		portionFraction: string;
		portionPercent: number;
		nominal: number;
		nominalPerPerson: number;
	}

	let inheritanceDistribution = $derived.by<HeirShare[]>(() => {
		const nw = currentNetWorth;
		const totalChildren = sonsCount + daughtersCount;

		if (regime === 'kuhperdata') {
			// KUHPerdata Pasal 852: Suami/Istri yang hidup terlama + anak mewarisi sama rata (Golongan I)
			const numHeirs = (hasSpouse ? 1 : 0) + totalChildren;
			if (numHeirs === 0) {
				return [
					{
						role: 'Orang Tua / Saudara Kandung',
						count: 1,
						portionFraction: '1/1',
						portionPercent: 1.0,
						nominal: nw,
						nominalPerPerson: nw
					}
				];
			}
			const equalShare = 1.0 / numHeirs;
			const list: HeirShare[] = [];
			if (hasSpouse) {
				list.push({
					role: spouseGender === 'wife' ? 'Istri' : 'Suami',
					count: 1,
					portionFraction: `1/${numHeirs}`,
					portionPercent: equalShare,
					nominal: nw * equalShare,
					nominalPerPerson: nw * equalShare
				});
			}
			if (sonsCount > 0) {
				const share = equalShare * sonsCount;
				list.push({
					role: 'Anak Laki-laki',
					count: sonsCount,
					portionFraction: `${sonsCount}/${numHeirs}`,
					portionPercent: share,
					nominal: nw * share,
					nominalPerPerson: (nw * share) / sonsCount
				});
			}
			if (daughtersCount > 0) {
				const share = equalShare * daughtersCount;
				list.push({
					role: 'Anak Perempuan',
					count: daughtersCount,
					portionFraction: `${daughtersCount}/${numHeirs}`,
					portionPercent: share,
					nominal: nw * share,
					nominalPerPerson: (nw * share) / daughtersCount
				});
			}
			return list;
		}

		// KHI (Kompilasi Hukum Islam / Faraidh).
		// Dengan anak:
		//   Istri 1/8, Suami 1/4, Ayah 1/6, Ibu 1/6, sisa = asabah anak (2:1).
		// Tanpa anak:
		//   Istri 1/4, Suami 1/2, Ibu 1/3 dari SISA setelah pasangan, dan Ayah
		//   mengambil sisa sebagai asabah. Sebelumnya Ayah dan Ibu masing-masing
		//   diberi 1/3 sehingga total hanya 91,67% dan sisa 1/12 hilang.
		const hasChildren = totalChildren > 0;

		let spousePct = 0;
		let spouseFraction = '0';
		if (hasSpouse) {
			if (spouseGender === 'wife') {
				spousePct = hasChildren ? 1 / 8 : 1 / 4;
				spouseFraction = hasChildren ? '1/8 (12,5%)' : '1/4 (25%)';
			} else {
				spousePct = hasChildren ? 1 / 4 : 1 / 2;
				spouseFraction = hasChildren ? '1/4 (25%)' : '1/2 (50%)';
			}
		}

		let fatherPct = 0;
		let motherPct = 0;
		let sonShareTotal = 0;
		let daughterShareTotal = 0;
		let fatherAsabah = false;

		if (hasChildren) {
			// Ayah & Ibu masing-masing 1/6 (karena ada anak).
			fatherPct = hasLivingFather ? 1 / 6 : 0;
			motherPct = hasLivingMother ? 1 / 6 : 0;

			const remainingAsabah = Math.max(0, 1.0 - spousePct - fatherPct - motherPct);
			// Asabah anak: laki-laki 2 bagian, perempuan 1 bagian (rasio 2:1).
			const childUnits = sonsCount * 2 + daughtersCount * 1;
			if (childUnits > 0) {
				sonShareTotal = (remainingAsabah * (sonsCount * 2)) / childUnits;
				daughterShareTotal = (remainingAsabah * (daughtersCount * 1)) / childUnits;
			} else if (hasLivingFather) {
				// Tak ada anak: sisa jatuh ke ayah sebagai asabah.
				fatherPct += remainingAsabah;
				fatherAsabah = true;
			}
		} else {
			// Tanpa anak: Ibu 1/3 dari sisa (setelah bagian pasangan),
			// Ayah mengambil sisanya sebagai asabah — total selalu 100%.
			const afterSpouse = Math.max(0, 1.0 - spousePct);
			if (hasLivingMother && hasLivingFather) {
				motherPct = afterSpouse / 3;
				fatherPct = afterSpouse - motherPct;
				fatherAsabah = true;
			} else if (hasLivingMother) {
				motherPct = afterSpouse / 3;
			} else if (hasLivingFather) {
				fatherPct = afterSpouse;
				fatherAsabah = true;
			}
		}

		const list: HeirShare[] = [];
		if (hasSpouse) {
			list.push({
				role: spouseGender === 'wife' ? 'Istri' : 'Suami',
				count: 1,
				portionFraction: spouseFraction,
				portionPercent: spousePct,
				nominal: nw * spousePct,
				nominalPerPerson: nw * spousePct
			});
		}
		if (hasLivingFather && fatherPct > 0) {
			list.push({
				role: 'Ayah Kandung',
				count: 1,
				portionFraction: fatherAsabah ? `Asabah (${percent(fatherPct, 1)})` : '1/6 (16,7%)',
				portionPercent: fatherPct,
				nominal: nw * fatherPct,
				nominalPerPerson: nw * fatherPct
			});
		}
		if (hasLivingMother && motherPct > 0) {
			list.push({
				role: 'Ibu Kandung',
				count: 1,
				portionFraction: hasChildren ? '1/6 (16,7%)' : `1/3 sisa (${percent(motherPct, 1)})`,
				portionPercent: motherPct,
				nominal: nw * motherPct,
				nominalPerPerson: nw * motherPct
			});
		}
		if (sonsCount > 0) {
			list.push({
				role: 'Anak Laki-laki (Bagian 2x)',
				count: sonsCount,
				portionFraction: `Asabah (${percent(sonShareTotal, 1)})`,
				portionPercent: sonShareTotal,
				nominal: nw * sonShareTotal,
				nominalPerPerson: sonShareTotal > 0 ? (nw * sonShareTotal) / sonsCount : 0
			});
		}
		if (daughtersCount > 0) {
			list.push({
				role: 'Anak Perempuan (Bagian 1x)',
				count: daughtersCount,
				portionFraction: `Asabah (${percent(daughterShareTotal, 1)})`,
				portionPercent: daughterShareTotal,
				nominal: nw * daughterShareTotal,
				nominalPerPerson: daughterShareTotal > 0 ? (nw * daughterShareTotal) / daughtersCount : 0
			});
		}

		// Radd: bila masih ada sisa setelah bagian tetap dan TIDAK ada asabah
		// (mis. hanya istri + ibu tanpa ayah/anak), kembalikan sisa secara
		// proporsional agar total selalu 100%. Tanpa ini warisan bisa hanya
		// terbagi 50% dan sisanya "hilang".
		const allocated = list.reduce((s, h) => s + h.portionPercent, 0);
		const leftover = 1.0 - allocated;
		if (leftover > 1e-9 && list.length > 0) {
			// Utamakan penerima non-pasangan (sesuai kaidah radd klasik).
			const nonSpouse = list.filter((h) => h.role !== 'Istri' && h.role !== 'Suami');
			const pool = nonSpouse.length ? nonSpouse : list;
			const base = pool.reduce((s, h) => s + h.portionPercent, 0);
			for (const h of pool) {
				const add = base > 0 ? (h.portionPercent / base) * leftover : leftover / pool.length;
				h.portionPercent += add;
				h.nominal = nw * h.portionPercent;
				h.nominalPerPerson = h.count > 0 ? h.nominal / h.count : h.nominal;
			}
		}
		return list;
	});

	// Estimasi Kebutuhan Dana Likuiditas Cepat (Estate Liquidity Buffer)
	// Rekening bank dibekukan 3-6 bulan; kebutuhan keluarga ~6 bulan pengeluaran
	let monthlyLivingCost = $derived(profile?.expense_monthly ?? 6_000_000);
	let emergencyEstateLiquidityNeeded = $derived(monthlyLivingCost * 6);
</script>

<div class="card p-5">
	<!-- Header -->
	<div
		class="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--color-line)] pb-4"
	>
		<div>
			<div class="flex items-center gap-2">
				<span class="text-xl">📜</span>
				<h3 class="text-base font-bold text-[var(--color-ink)]">
					Simulator Perencanaan Waris & Proteksi Likuiditas Keluarga (Estate Planning)
				</h3>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Simulasi proyeksi pembagian hak waris sesuai Kompilasi Hukum Islam (KHI/Faraidh) atau
				KUHPerdata, serta mitigasi risiko rekening beku perbankan.
			</p>
		</div>

		<!-- Pemilihan Rezim Hukum -->
		<div
			class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs"
		>
			<button
				class="rounded-md px-3 py-1 font-semibold transition {regime === 'khi'
					? 'bg-[var(--color-accent)] text-white'
					: 'text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]'}"
				onclick={() => (regime = 'khi')}
			>
				Faraidh Syariah (KHI)
			</button>
			<button
				class="rounded-md px-3 py-1 font-semibold transition {regime === 'kuhperdata'
					? 'bg-[var(--color-accent)] text-white'
					: 'text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]'}"
				onclick={() => (regime = 'kuhperdata')}
			>
				Hukum Perdata (KUHPerdata)
			</button>
		</div>
	</div>

	<!-- Kontrol Twin & Horizon Tahun Proyeksi -->
	<div class="mt-4 flex flex-wrap items-center justify-between gap-3">
		<div class="flex flex-wrap items-center gap-2 text-xs">
			<span class="font-semibold text-[var(--color-ink-dim)]">Skenario Twin:</span>
			<select
				class="rounded-lg border border-[var(--color-line)] bg-[var(--color-void-1)] px-2.5 py-1 text-xs font-semibold text-[var(--color-ink)]"
				bind:value={selectedTwinCode}
			>
				{#each twins as t}
					<option value={t.code}>Twin {t.code}: {t.label}</option>
				{/each}
			</select>
		</div>

		<div class="flex items-center gap-2 text-xs">
			<span class="font-semibold text-[var(--color-ink-dim)]">Tahun Evaluasi:</span>
			<div
				class="flex rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-0.5 text-xs"
			>
				{#each [5, 10, 20] as y}
					<button
						class="rounded-md px-2.5 py-1 font-semibold transition {year === y
							? 'bg-[var(--color-accent)] text-white'
							: 'text-[var(--color-ink-dim)]'}"
						onclick={() => (year = y)}
					>
						Th-{y}
					</button>
				{/each}
			</div>
		</div>
	</div>

	<!-- Parameter Ahli Waris Keluarga -->
	<div class="mt-4 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-4">
		<span class="text-xs font-bold text-[var(--color-ink)]"
			>Komposisi Ahli Waris yang Ditinggalkan:</span
		>
		<div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6 text-xs">
			<label class="flex items-center gap-2 cursor-pointer">
				<input type="checkbox" class="rounded" bind:checked={hasSpouse} />
				<span>Ada Pasangan</span>
			</label>

			{#if hasSpouse}
				<div>
					<select
						class="w-full rounded border border-[var(--color-line)] bg-[var(--color-void-2)] px-2 py-1 text-xs"
						bind:value={spouseGender}
					>
						<option value="wife">Istri (Pewaris Suami)</option>
						<option value="husband">Suami (Pewaris Istri)</option>
					</select>
				</div>
			{/if}

			<div>
				<span class="block text-[11px] text-[var(--color-ink-dim)]">Anak Laki-laki:</span>
				<input
					type="number"
					class="w-full rounded border border-[var(--color-line)] bg-[var(--color-void-2)] px-2 py-1 font-mono text-xs font-bold"
					min="0"
					max="6"
					bind:value={sonsCount}
				/>
			</div>

			<div>
				<span class="block text-[11px] text-[var(--color-ink-dim)]">Anak Perempuan:</span>
				<input
					type="number"
					class="w-full rounded border border-[var(--color-line)] bg-[var(--color-void-2)] px-2 py-1 font-mono text-xs font-bold"
					min="0"
					max="6"
					bind:value={daughtersCount}
				/>
			</div>

			<label class="flex items-center gap-2 cursor-pointer">
				<input type="checkbox" class="rounded" bind:checked={hasLivingFather} />
				<span>Ayah Hidup</span>
			</label>

			<label class="flex items-center gap-2 cursor-pointer">
				<input type="checkbox" class="rounded" bind:checked={hasLivingMother} />
				<span>Ibu Hidup</span>
			</label>
		</div>
	</div>

	<!-- Rincian Proyeksi Harta Waris -->
	<div class="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
		<!-- Ringkasan Nilai Harta Bersih -->
		<div
			class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4 flex flex-col justify-between"
		>
			<div>
				<span class="text-xs font-semibold text-[var(--color-ink-dim)]">
					Proyeksi Harta Waris Bersih ({currentTwin?.label ?? 'Twin'}, Th-{year}):
				</span>
				<div class="mt-1 text-2xl font-extrabold text-[var(--color-accent)]">
					{rupiah(currentNetWorth)}
				</div>
				<p class="mt-2 text-[11px] leading-relaxed text-[var(--color-ink-dim)]">
					{#if regime === 'khi'}
						Berdasarkan Pasal 171–191 Kompilasi Hukum Islam (KHI). Harta peninggalan dibagi setelah
						pelunasan utang almarhum dan pemenuhan wasiat (maksimal 1/3 harta).
					{:else}
						Berdasarkan Kitab Undang-Undang Hukum Perdata (KUHPerdata Pasal 852). Ahli waris
						Golongan I mewarisi secara proporsional sama rata.
					{/if}
				</p>
			</div>

			<!-- Peringatan Pembekuan Rekening Bank (Estate Liquidity Risk) -->
			<div class="mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs">
				<div class="flex items-center gap-1.5 font-bold text-amber-400">
					<span>⚠️</span>
					<span>Risiko Pembekuan Rekening Bank</span>
				</div>
				<p class="mt-1 text-[11px] leading-relaxed text-[var(--color-ink-dim)]">
					Saat nasabah wafat, rekening bank & sekuritas dibekukan otomatis oleh perbankan hingga ada
					Surat Keterangan Hak Waris (SKHW) notaris (3–6 bulan).
				</p>
				<div class="mt-2 flex justify-between border-t border-amber-500/20 pt-1.5 text-[11px]">
					<span class="text-[var(--color-ink-dim)]">Kebutuhan Dana Cepat (6 bln):</span>
					<strong class="text-amber-300">{rupiahBrief(emergencyEstateLiquidityNeeded)}</strong>
				</div>
			</div>
		</div>

		<!-- Tabel Pembagian Hak Waris Tiap Anggota Keluarga -->
		<div
			class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-4 lg:col-span-2"
		>
			<span class="text-xs font-bold text-[var(--color-ink)]">
				Simulasi Alokasi Warisan Tiap Ahli Waris ({regime === 'khi'
					? 'KHI / Faraidh Syariah'
					: 'KUHPerdata Golongan I'}):
			</span>

			<div class="mt-3 overflow-x-auto">
				<table class="w-full text-left text-xs">
					<thead>
						<tr class="border-b border-[var(--color-line)] text-[var(--color-ink-dim)] text-[11px]">
							<th scope="col" class="pb-2 font-semibold">Ahli Waris</th>
							<th scope="col" class="pb-2 font-semibold">Jumlah</th>
							<th scope="col" class="pb-2 font-semibold">Porsi Hukum</th>
							<th scope="col" class="pb-2 font-semibold">Nominal Total</th>
							<th scope="col" class="pb-2 font-semibold">Per Orang</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-[var(--color-line)]/50">
						{#each inheritanceDistribution as heir}
							<tr>
								<td class="py-2.5 font-semibold text-[var(--color-ink)]">{heir.role}</td>
								<td class="py-2.5">{heir.count} orang</td>
								<td class="py-2.5 font-mono text-cyan-400">{heir.portionFraction}</td>
								<td class="py-2.5 font-bold text-[var(--color-ink)]">{rupiahBrief(heir.nominal)}</td
								>
								<td class="py-2.5 font-mono font-semibold text-emerald-400"
									>{rupiah(heir.nominalPerPerson)}</td
								>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Best Practice Solusi Likuiditas Waris -->
			<div
				class="mt-4 border-t border-[var(--color-line)] pt-3 text-[11px] text-[var(--color-ink-dim)]"
			>
				<span class="font-bold text-[var(--color-ink)]">💡 Solusi Perencanaan Waris Aman:</span>
				Miliki <strong>Asuransi Jiwa Murni / Syariah</strong> dengan *Beneficiary Designation*
				setara dana darurat keluarga ({rupiahBrief(emergencyEstateLiquidityNeeded)}). Uang
				pertanggungan asuransi jiwa <strong>bukan objek sengketa waris</strong> dan langsung cair dalam
				7–14 hari kerja tanpa proses SKHW notaris.
			</div>
		</div>
	</div>
</div>
