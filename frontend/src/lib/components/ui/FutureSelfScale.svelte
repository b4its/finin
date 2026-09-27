<script lang="ts">
	/** Skala Future Self-Continuity (Hershfield dkk., 2011).
	 *
	 * Menampilkan visualisasi 7 pasang lingkaran Euler (Saya Sekarang vs Saya Masa Depan)
	 * dengan tingkat overlap dari 1 (terpisah total) hingga 7 (hampir menyatu).
	 */

	let {
		value = $bindable<number | null>(null),
		compact = false,
		onchange
	}: {
		value?: number | null;
		compact?: boolean;
		onchange?: (v: number) => void;
	} = $props();

	const LABELS = [
		'Sangat Terpisah — belum terbayang dirimu di 10–20 tahun ke depan',
		'Kurang Terhubung — masa depan terasa masih sangat jauh',
		'Mulai Terbayang — sesekali memikirkan rencana jangka panjang',
		'Cukup Terhubung — sudah mulai menimbang masa depan dalam keputusan',
		'Terhubung — aktif mempersiapkan dana dan target masa depan',
		'Sangat Dekat — masa depan jadi pertimbangan utama setiap bulan',
		'Satu Kesatuan — keputusan hari ini sepenuhnya selaras demi diri masa depan'
	];

	// Jarak antar pusat lingkaran (r = 18px), lebar total 72px, pusat Y = 24px
	// Titik 1: c1 = 18, c2 = 54 (gap 18px antar sisi)
	// Titik 7: c1 = 33, c2 = 39 (overlap hampir penuh)
	const OVERLAPS = [
		{ c1: 18, c2: 54 }, // 1: pisah jauh
		{ c1: 21, c2: 51 }, // 2: menyentuh
		{ c1: 24, c2: 48 }, // 3: overlap tipis
		{ c1: 27, c2: 45 }, // 4: overlap sedang
		{ c1: 30, c2: 42 }, // 5: overlap dalam
		{ c1: 33, c2: 39 }, // 6: overlap sangat dalam
		{ c1: 35, c2: 37 } // 7: hampir menyatu
	];

	function select(v: number) {
		value = v;
		onchange?.(v);
	}
</script>

<div class="space-y-3">
	<div class="grid grid-cols-2 gap-2 sm:grid-cols-4 md:grid-cols-7">
		{#each [1, 2, 3, 4, 5, 6, 7] as v}
			{@const geom = OVERLAPS[v - 1]}
			{@const isSelected = value === v}
			<button
				type="button"
				class="group flex flex-col items-center rounded-xl border p-2 transition-all text-center {isSelected
					? 'border-[var(--color-accent)] bg-blue-500/10'
					: 'border-[var(--color-line)] hover:border-[var(--color-ink-dim)]'}"
				onclick={() => select(v)}
				aria-pressed={isSelected}
				aria-label={`Skala ${v} dari 7: ${LABELS[v - 1]}`}
			>
				<svg
					viewBox="0 0 72 48"
					class="h-10 w-16 transition-transform group-hover:scale-105"
					aria-hidden="true"
				>
					<!-- Lingkaran Saya Sekarang -->
					<circle
						cx={geom.c1}
						cy="24"
						r="16"
						fill={isSelected ? '#38BDF8' : '#94A3B8'}
						fill-opacity={isSelected ? '0.35' : '0.15'}
						stroke={isSelected ? '#38BDF8' : '#94A3B8'}
						stroke-width="1.8"
					/>
					<text
						x={geom.c1}
						y="27"
						text-anchor="middle"
						class="text-[8px] font-bold fill-current"
						fill={isSelected ? '#38BDF8' : '#94A3B8'}>Kini</text
					>

					<!-- Lingkaran Saya Masa Depan -->
					<circle
						cx={geom.c2}
						cy="24"
						r="16"
						fill={isSelected ? '#818CF8' : '#64748B'}
						fill-opacity={isSelected ? '0.35' : '0.15'}
						stroke={isSelected ? '#818CF8' : '#64748B'}
						stroke-width="1.8"
						stroke-dasharray="2,2"
					/>
					<text
						x={geom.c2}
						y="27"
						text-anchor="middle"
						class="text-[8px] font-bold fill-current"
						fill={isSelected ? '#818CF8' : '#64748B'}>Nanti</text
					>
				</svg>

				<div class="mt-1 flex items-center justify-center gap-1">
					<span
						class="flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold transition-colors"
						class:bg-[var(--color-accent)]={isSelected}
						class:text-[var(--color-void)]={isSelected}
						class:bg-[var(--color-void-3)]={!isSelected}
						class:text-[var(--color-ink-dim)]={!isSelected}
					>
						{v}
					</span>
				</div>
			</button>
		{/each}
	</div>

	{#if value !== null && !compact}
		<div
			class="rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-2.5 text-center"
		>
			<span class="text-xs font-semibold text-[var(--color-accent)]">Skor {value}/7:</span>
			<span class="ml-1 text-xs text-[var(--color-ink)]">{LABELS[value - 1]}</span>
		</div>
	{/if}
</div>
