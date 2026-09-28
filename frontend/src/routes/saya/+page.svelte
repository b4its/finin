<script lang="ts">
	import { onMount } from 'svelte';
	import { history } from '$lib/stores/history.svelte';
	import { toast } from '$lib/stores/toast.svelte';
	import { dateID } from '$lib/utils/format';
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';

	onMount(() => history.load());

	let query = $state('');
	let presetFilter = $state<string>('semua');
	let sortBy = $state<'terbaru' | 'terlama' | 'cabang' | 'preset'>('terbaru');
	let confirmClear = $state(false);

	function remove(id: string) {
		history.remove(id);
		toast.info('Simulasi dihapus dari riwayat');
	}

	function clearAll() {
		if (!confirmClear) {
			confirmClear = true;
			setTimeout(() => (confirmClear = false), 4000);
			return;
		}
		history.clear();
		confirmClear = false;
		toast.info('Riwayat simulasi dikosongkan');
	}

	/** Daftar preset unik yang muncul di riwayat (untuk filter). */
	let presets = $derived([...new Set(history.items.map((r) => r.preset))].sort());

	let filtered = $derived.by(() => {
		const q = query.trim().toLowerCase();
		const rows = history.items.filter((r) => {
			const matchPreset = presetFilter === 'semua' || r.preset === presetFilter;
			const matchQuery =
				!q ||
				(r.label ?? '').toLowerCase().includes(q) ||
				r.id.toLowerCase().includes(q) ||
				r.best_twin.toLowerCase().includes(q);
			return matchPreset && matchQuery;
		});
		const sorted = [...rows];
		switch (sortBy) {
			case 'terlama':
				sorted.sort((a, b) => a.created_at - b.created_at);
				break;
			case 'cabang':
				sorted.sort((a, b) => b.twin_count - a.twin_count);
				break;
			case 'preset':
				sorted.sort((a, b) => a.preset.localeCompare(b.preset) || b.created_at - a.created_at);
				break;
			default:
				sorted.sort((a, b) => b.created_at - a.created_at);
		}
		return sorted;
	});

	/** Ringkasan cepat riwayat. */
	let stats = $derived.by(() => {
		const items = history.items;
		if (!items.length) return null;
		const twinCounts: Record<string, number> = {};
		for (const it of items) twinCounts[it.best_twin] = (twinCounts[it.best_twin] ?? 0) + 1;
		const top = Object.entries(twinCounts).sort((a, b) => b[1] - a[1])[0];
		return {
			total: items.length,
			lastAt: items.reduce((m, r) => Math.max(m, r.created_at), 0),
			topTwin: top?.[0] ?? '—',
			topTwinCount: top?.[1] ?? 0,
			avgBranches: (items.reduce((s, r) => s + r.twin_count, 0) / items.length).toFixed(1)
		};
	});
</script>

<svelte:head><title>Simulasi saya — Financial Twin</title></svelte:head>

<div class="mx-auto max-w-3xl px-4 py-8 sm:px-5">
	<div class="flex flex-wrap items-start justify-between gap-3">
		<div>
			<h1 class="text-2xl font-bold">🗂️ Simulasi saya</h1>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Riwayat tersimpan di perangkatmu saja (tanpa akun, tanpa server).
			</p>
		</div>
		<div class="flex items-center gap-2">
			<a href="/start" class="btn btn-primary !py-1.5 !text-xs">+ Simulasi baru</a>
			{#if history.items.length}
				<button
					class="btn btn-ghost !py-1.5 !text-xs {confirmClear
						? '!border-[var(--color-danger)] !text-[var(--color-danger)]'
						: 'text-[var(--color-ink-dim)]'}"
					onclick={clearAll}
				>
					{confirmClear ? 'Yakin? Klik lagi' : 'Kosongkan'}
				</button>
			{/if}
		</div>
	</div>

	{#if stats}
		<section class="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4" aria-label="Ringkasan riwayat">
			<div class="card p-3 text-center">
				<div class="num text-xl font-bold">{stats.total}</div>
				<div class="text-[11px] text-[var(--color-ink-dim)]">simulasi tersimpan</div>
			</div>
			<div class="card p-3 text-center">
				<div class="num text-xl font-bold">{stats.avgBranches}</div>
				<div class="text-[11px] text-[var(--color-ink-dim)]">rata-rata cabang</div>
			</div>
			<div class="card p-3 text-center">
				<div class="num text-xl font-bold">{stats.topTwin}</div>
				<div class="text-[11px] text-[var(--color-ink-dim)]">twin terbaik tersering</div>
			</div>
			<div class="card p-3 text-center">
				<div class="text-sm font-semibold">
					{stats.lastAt ? dateID(new Date(stats.lastAt).toISOString()) : '—'}
				</div>
				<div class="text-[11px] text-[var(--color-ink-dim)]">terakhir dibuat</div>
			</div>
		</section>

		<div class="mt-5 flex flex-wrap items-center gap-2">
			<div class="relative min-w-[12rem] flex-1">
				<span
					class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[var(--color-ink-faint)]"
					aria-hidden="true">🔍</span
				>
				<input
					class="input !pl-9"
					type="search"
					placeholder="Cari label, ID, atau twin…"
					bind:value={query}
					aria-label="Cari riwayat simulasi"
				/>
			</div>
			<label class="flex items-center gap-1.5 text-xs text-[var(--color-ink-dim)]">
				Preset
				<select
					class="input !w-auto !py-1.5 !text-xs"
					bind:value={presetFilter}
					aria-label="Filter berdasarkan preset"
				>
					<option value="semua">Semua</option>
					{#each presets as p}<option value={p}>{p}</option>{/each}
				</select>
			</label>
			<label class="flex items-center gap-1.5 text-xs text-[var(--color-ink-dim)]">
				Urut
				<select
					class="input !w-auto !py-1.5 !text-xs"
					bind:value={sortBy}
					aria-label="Urutkan riwayat"
				>
					<option value="terbaru">Terbaru</option>
					<option value="terlama">Terlama</option>
					<option value="cabang">Terbanyak cabang</option>
					<option value="preset">Preset</option>
				</select>
			</label>
		</div>
	{/if}

	<div class="mt-5 space-y-3">
		{#if filtered.length}
			{#each filtered as r (r.id)}
				<div class="card card-interactive flex items-center justify-between gap-3 p-4">
					<a href={`/sim/${r.id}`} class="min-w-0 flex-1">
						<p class="truncate text-sm font-semibold">
							{r.label || `Simulasi ${r.id.slice(0, 8)}`}
						</p>
						<p class="mt-0.5 text-xs text-[var(--color-ink-dim)]">
							{r.twin_count} cabang · twin terbaik
							<strong class="text-[var(--color-ink)]">{r.best_twin}</strong>
							· preset {r.preset} · {dateID(new Date(r.created_at).toISOString())}
						</p>
					</a>
					<div class="flex shrink-0 items-center gap-1.5">
						<a href={`/sim/${r.id}`} class="btn btn-ghost !px-3 !py-1.5 !text-xs">Buka</a>
						<button
							class="btn btn-ghost !px-2.5 !py-1.5 !text-xs text-[var(--color-ink-dim)]"
							aria-label={`Hapus riwayat ${r.label || r.id}`}
							onclick={() => remove(r.id)}>✕</button
						>
					</div>
				</div>
			{/each}
		{:else if history.items.length}
			<div class="card p-8 text-center">
				<p class="text-3xl" aria-hidden="true">🔎</p>
				<p class="mt-3 font-semibold">Tidak ada simulasi yang cocok</p>
				<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
					Ubah kata kunci atau filter preset untuk menemukan riwayatmu.
				</p>
				<button
					class="btn btn-ghost mt-4"
					onclick={() => {
						query = '';
						presetFilter = 'semua';
					}}>Reset filter</button
				>
			</div>
		{:else}
			<div class="card p-8 text-center">
				<p class="text-3xl" aria-hidden="true">🌌</p>
				<p class="mt-3 font-semibold">Belum ada simulasi tersimpan</p>
				<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
					Mulai simulasi pertamamu dan hasilnya akan tercatat di sini.
				</p>
				<a href="/start" class="btn btn-primary mt-5 !px-6 !py-2.5">Mulai simulasi →</a>
			</div>
		{/if}
	</div>

	<div class="mt-8">
		<Disclaimer variant="compact" />
	</div>
</div>
