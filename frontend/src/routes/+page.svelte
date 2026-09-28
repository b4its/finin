<script lang="ts">
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';
	import FutureSelfScale from '$lib/components/ui/FutureSelfScale.svelte';
	import { sim } from '$lib/stores/simulation.svelte';
	import { api } from '$lib/api/client';
	import { onMount } from 'svelte';

	let market: { label: string; source: string }[] = $state([]);
	let impact = $state<{ commits: number; simulations: number; fsc_delta: number | null } | null>(
		null
	);

	const faqs = [
		{
			q: 'Apakah data saya aman?',
			a: 'Ya. Tidak ada akun, nama, maupun NIK. Simulasi diidentifikasi UUID anonim dan disimpan 30 hari (sesuai UU 27/2022 PDP). Riwayat juga tersimpan lokal di perangkatmu.'
		},
		{
			q: 'Apakah ini nasihat keuangan?',
			a: 'Bukan. Financial Twin adalah alat simulasi edukatif. Semua proyeksi bergantung pada asumsi dan tidak menjamin hasil. Konsultasikan keputusan penting dengan perencana keuangan berlisensi.'
		},
		{
			q: 'Dari mana angka-angkanya?',
			a: 'Semua angka dihitung mesin deterministik, bukan oleh AI. AI hanya menarasikan dan setiap angkanya divalidasi. Set asumsi berversi (ID-2026-09) dengan sumber OJK, BI, BPS, dan LPS — bisa kamu lihat dan edit.'
		},
		{
			q: 'Kenapa pakai aturan OJK?',
			a: 'Batas bunga pinjol (0,3%/hari tenor ≤6 bln, 0,2% >6 bln), lock cap 100% pokok, dan DSR 30% tertanam di engine. Kalau keputusanmu melanggar, sistem menandainya.'
		}
	];

	onMount(async () => {
		try {
			const a = await api.assumptions();
			market = a.market_context ?? [];
		} catch {
			market = [];
		}
		try {
			impact = await api.impactSummary();
		} catch {
			impact = null;
		}
	});
</script>

<svelte:head>
	<title>Financial Twin — lihat dirimu di 5, 10, dan 20 tahun</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-12 sm:px-5 sm:py-20">
	<section class="mt-6 text-center sm:mt-10">
		<div class="chip mx-auto border-[var(--color-accent)] text-[var(--color-accent)]">
			Berdasarkan data OJK, BI, BPS, LPS & riset Hershfield (2011)
		</div>
		<h1 class="mx-auto mt-5 max-w-3xl text-4xl font-extrabold leading-tight sm:text-5xl">
			Lihat <span class="text-[var(--color-accent)]">dirimu</span> di 5, 10, dan 20 tahun — sebelum kamu
			memutuskan.
		</h1>
		<p class="mx-auto mt-5 max-w-2xl text-lg text-[var(--color-ink-dim)]">
			Financial Twin membuat "kembaran digital" dari keputusanmu: pinjol/paylater, S2, atau dana
			darurat. Semua angka dihitung mesin deterministik, dengan aturan OJK tertanam.
		</p>
		<div class="mt-8 flex flex-wrap justify-center gap-3">
			<a href="/start" class="btn btn-primary !px-6 !py-3 !text-base">Bangun multiverse-ku →</a>
		</div>
		<p class="mt-3 text-xs text-[var(--color-ink-dim)]">
			Gratis · tanpa akun · selesai dalam &lt; 90 detik
		</p>

		<div
			class="mx-auto mt-10 max-w-xl rounded-2xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-5 text-left"
		>
			<div class="flex items-center justify-between gap-2">
				<div>
					<h3 class="text-sm font-semibold">🧬 Seberapa Dekat Kamu dengan Dirimu di Masa Depan?</h3>
					<p class="mt-0.5 text-xs text-[var(--color-ink-dim)]">
						Riset Hershfield (2011): keterhubungan visual dengan diri masa depan meningkatkan
						alokasi tabungan hingga 2× lipat.
					</p>
				</div>
				<span
					class="rounded-full bg-[var(--color-void-3)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-ink-dim)]"
					>Pra-simulasi</span
				>
			</div>
			<div class="mt-4">
				<FutureSelfScale bind:value={sim.fscPre} />
			</div>
		</div>
	</section>

	<section class="mt-16" aria-labelledby="how-heading">
		<h2 id="how-heading" class="text-center text-2xl font-bold">Cara kerjanya — 3 langkah</h2>
		<p class="mx-auto mt-2 max-w-xl text-center text-sm text-[var(--color-ink-dim)]">
			Tanpa akun, tanpa unggah data. Semua perhitungan transparan dan bisa diaudit.
		</p>
		<ol class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
			<li class="card relative p-5">
				<span
					class="num absolute right-4 top-4 text-3xl font-black text-[var(--color-void-3)]"
					aria-hidden="true">1</span
				>
				<div class="text-2xl" aria-hidden="true">📝</div>
				<h3 class="mt-2 font-bold">Ceritakan posisimu</h3>
				<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
					Pilih jenis penghasilan, tanggungan, utang berjalan, dan 1–2 keputusan besar yang sedang
					kamu timbang.
				</p>
			</li>
			<li class="card relative p-5">
				<span
					class="num absolute right-4 top-4 text-3xl font-black text-[var(--color-void-3)]"
					aria-hidden="true">2</span
				>
				<div class="text-2xl" aria-hidden="true">⚙️</div>
				<h3 class="mt-2 font-bold">Engine menghitung 240 bulan</h3>
				<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
					Mesin deterministik memproyeksikan setiap cabang lintas 3 preset asumsi, plus uji
					guncangan dan aturan OJK.
				</p>
			</li>
			<li class="card relative p-5">
				<span
					class="num absolute right-4 top-4 text-3xl font-black text-[var(--color-void-3)]"
					aria-hidden="true">3</span
				>
				<div class="text-2xl" aria-hidden="true">🌌</div>
				<h3 class="mt-2 font-bold">Bandingkan multiverse-mu</h3>
				<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
					Lihat kembaran digitalmu berdampingan, temukan rekomendasi, lalu komit langkah pertama
					hari ini.
				</p>
			</li>
		</ol>
	</section>

	{#if impact && impact.commits > 0}
		<section class="mt-12 grid grid-cols-1 gap-4 sm:grid-cols-3">
			<div class="card p-4 text-center">
				<div class="num text-2xl font-bold">{impact.simulations}</div>
				<div class="text-xs text-[var(--color-ink-dim)]">simulasi dibuat</div>
			</div>
			<div class="card p-4 text-center">
				<div class="num text-2xl font-bold">{impact.commits}</div>
				<div class="text-xs text-[var(--color-ink-dim)]">komitmen langkah</div>
			</div>
			<div class="card p-4 text-center">
				<div class="num text-2xl font-bold">
					{impact.fsc_delta !== null
						? (impact.fsc_delta > 0 ? '+' : '') + impact.fsc_delta.toFixed(1)
						: '—'}
				</div>
				<div class="text-xs text-[var(--color-ink-dim)]">Δ kedekatan diri masa depan</div>
			</div>
		</section>
	{/if}

	<section class="mt-16">
		<h2 class="text-center text-2xl font-bold">Masalahnya nyata dan terukur</h2>
		<div class="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
			{#each market as m}
				<div class="card flex items-start gap-3 p-4">
					<span class="text-[var(--color-accent)]">▸</span>
					<div>
						<p class="text-sm">{m.label}</p>
						<p class="mt-0.5 text-xs text-[var(--color-ink-dim)]">Sumber: {m.source}</p>
					</div>
				</div>
			{:else}
				<div class="card p-4 text-sm text-[var(--color-ink-dim)]">Memuat data konteks pasar…</div>
			{/each}
		</div>
	</section>

	<section class="mt-16 grid grid-cols-1 gap-4 sm:grid-cols-3">
		<div class="card p-5">
			<div class="text-2xl">🧬</div>
			<h3 class="mt-2 font-bold">Dasar ilmiah</h3>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Future self-continuity: orang yang melihat versi tua dirinya menabung &gt; 2× lebih banyak
				(Hershfield dkk., 2011).
			</p>
		</div>
		<div class="card p-5">
			<div class="text-2xl">⚖️</div>
			<h3 class="mt-2 font-bold">Regulasi OJK</h3>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Batas bunga pinjol 0,3%/hari (tenor ≤6 bln), lock cap 100% pokok, DSR 30% — tertanam di
				engine.
			</p>
		</div>
		<div class="card p-5">
			<div class="text-2xl">🔍</div>
			<h3 class="mt-2 font-bold">Transparan</h3>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Setiap asumsi punya nilai, tanggal, dan tautan sumber. LLM hanya menarasikan — tidak
				menghitung.
			</p>
		</div>
	</section>

	<section class="mt-16" aria-labelledby="faq-heading">
		<h2 id="faq-heading" class="text-center text-2xl font-bold">Pertanyaan yang sering diajukan</h2>
		<div class="mx-auto mt-6 max-w-2xl space-y-3">
			{#each faqs as f}
				<details class="card group p-4">
					<summary
						class="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-semibold"
					>
						<span>{f.q}</span>
						<span
							class="text-[var(--color-ink-dim)] transition-transform group-open:rotate-45"
							aria-hidden="true">+</span
						>
					</summary>
					<p class="mt-2 text-sm leading-relaxed text-[var(--color-ink-dim)]">{f.a}</p>
				</details>
			{/each}
		</div>
	</section>

	<section class="mt-16">
		<Disclaimer />
	</section>

	<div class="mt-10 text-center">
		<a href="/start" class="btn btn-primary !px-6 !py-3 !text-base">Mulai sekarang →</a>
	</div>
</div>
