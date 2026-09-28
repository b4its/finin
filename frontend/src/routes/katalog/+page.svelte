<script lang="ts">
	/**
	 * Katalog keputusan: memuat seluruh template dari backend (GET /templates)
	 * dan menampilkan persona kembar + data yang dibutuhkan tiap template.
	 * Pengguna bisa langsung melompat ke wizard dengan template terpilih.
	 */
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import type { DecisionTemplate } from '$lib/api/types';
	import { twinIcon } from '$lib/utils/icons';
	import {
		buildCatalog,
		CATEGORY_LABELS,
		fieldTypeLabel,
		type CatalogCategory
	} from '$lib/data/catalog';
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';

	let templates = $state<DecisionTemplate[]>([]);
	let loading = $state(true);
	let errorMsg = $state<string | null>(null);
	let query = $state('');
	let category = $state<CatalogCategory | 'semua'>('semua');

	onMount(async () => {
		try {
			const res = await api.templates();
			templates = res.templates ?? [];
		} catch (e) {
			errorMsg = String(e);
		} finally {
			loading = false;
		}
	});

	let rows = $derived(buildCatalog(templates, query, category));
	let categories = $derived(Object.entries(CATEGORY_LABELS) as [CatalogCategory, string][]);
	let counts = $derived.by(() => {
		const map: Record<string, number> = {};
		for (const t of templates) {
			const cat = buildCatalog([t], '', 'semua')[0]?.category ?? 'karier';
			map[cat] = (map[cat] ?? 0) + 1;
		}
		return map;
	});
</script>

<svelte:head><title>Katalog keputusan — Financial Twin</title></svelte:head>

<div class="mx-auto max-w-6xl px-4 py-8 sm:px-5">
	<header class="text-center">
		<div class="chip mx-auto border-[var(--color-accent)] text-[var(--color-accent)]">
			{templates.length || 13} template keputusan
		</div>
		<h1 class="mx-auto mt-4 max-w-2xl text-2xl font-bold sm:text-3xl">
			Katalog keputusan finansial
		</h1>
		<p class="mx-auto mt-2 max-w-xl text-sm text-[var(--color-ink-dim)]">
			Setiap template memasangkan dua "kembaran" masa depanmu. Jelajahi, lalu buka langsung di
			wizard untuk melihat proyeksinya.
		</p>
	</header>

	<div class="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<div class="relative flex-1">
			<span
				class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[var(--color-ink-faint)]"
				aria-hidden="true">🔍</span
			>
			<input
				class="input !pl-9"
				type="search"
				placeholder="Cari keputusan (mis. pinjol, rumah, haji)…"
				bind:value={query}
				aria-label="Cari template keputusan"
			/>
		</div>
	</div>

	<div class="mt-4 flex flex-wrap gap-1.5" role="group" aria-label="Saring kategori">
		<button
			type="button"
			class="chip chip-activate"
			class:active={category === 'semua'}
			onclick={() => (category = 'semua')}
		>
			Semua ({templates.length})
		</button>
		{#each categories as [key, label] (key)}
			<button
				type="button"
				class="chip chip-activate"
				class:active={category === key}
				onclick={() => (category = key)}
			>
				{label} ({counts[key] ?? 0})
			</button>
		{/each}
	</div>

	{#if loading}
		<div class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy="true">
			{#each Array(6) as _}
				<div class="card h-48 skeleton"></div>
			{/each}
			<span class="sr-only">Memuat katalog keputusan…</span>
		</div>
	{:else if errorMsg}
		<div class="card mt-6 p-8 text-center">
			<p class="text-4xl" aria-hidden="true">🛰️</p>
			<h2 class="mt-3 text-lg font-bold">Katalog tidak dapat dimuat</h2>
			<p class="mx-auto mt-1 max-w-md text-sm text-[var(--color-ink-dim)]">
				Backend sedang tidak dapat dijangkau. Coba muat ulang halaman ini.
			</p>
			<code
				class="mx-auto mt-3 block max-w-md truncate rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] px-3 py-2 text-xs text-[var(--color-ink-dim)]"
				title={errorMsg}>{errorMsg}</code
			>
			<a href="/start" class="btn btn-primary mt-5">Mulai simulasi langsung</a>
		</div>
	{:else if !rows.length}
		<div class="card mt-6 p-8 text-center">
			<p class="text-3xl" aria-hidden="true">🔎</p>
			<p class="mt-3 font-semibold">Tidak ada keputusan yang cocok</p>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Ubah kata kunci atau pilih kategori lain.
			</p>
			<button
				class="btn btn-ghost mt-4"
				onclick={() => {
					query = '';
					category = 'semua';
				}}>Reset filter</button
			>
		</div>
	{:else}
		<p class="mt-4 text-xs text-[var(--color-ink-dim)]">
			Menampilkan {rows.length} dari {templates.length} keputusan.
		</p>
		<div class="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each rows as row (row.template.type)}
				<article class="card card-interactive flex flex-col p-5">
					<div class="flex items-start justify-between gap-3">
						<div class="flex items-center gap-2">
							<span class="text-2xl" aria-hidden="true">{row.icon}</span>
							<span class="chip">{CATEGORY_LABELS[row.category]}</span>
						</div>
					</div>
					<h2 class="mt-3 text-base font-bold leading-snug">{row.template.title}</h2>
					<p class="mt-1.5 flex-1 text-sm text-[var(--color-ink-dim)]">{row.blurb}</p>

					<div class="mt-3 grid grid-cols-2 gap-2">
						{#each [row.template.twin_a, row.template.twin_b] as twin}
							<div
								class="rounded-lg border border-[var(--color-line)] bg-[var(--color-void-2)] p-2.5"
							>
								<div class="flex items-center gap-1.5 text-[11px] text-[var(--color-ink-dim)]">
									<span aria-hidden="true">{twinIcon(twin.icon)}</span>
									<span>Kembar {twin.code}</span>
								</div>
								<div class="mt-0.5 truncate text-xs font-semibold" style="color:{twin.color}">
									{twin.label}
								</div>
							</div>
						{/each}
					</div>

					<div class="mt-3">
						<p class="text-[11px] uppercase tracking-wide text-[var(--color-ink-dim)]">
							Data dibutuhkan
						</p>
						<ul class="mt-1.5 space-y-1">
							{#each row.template.fields as f (f.key)}
								<li class="flex items-center justify-between gap-2 text-xs">
									<span class="truncate text-[var(--color-ink)]">{f.label}</span>
									<span class="chip shrink-0 !text-[0.65rem]">{fieldTypeLabel(f.type)}</span>
								</li>
							{/each}
						</ul>
					</div>

					<a
						href={`/start?template=${encodeURIComponent(row.template.type)}`}
						class="btn btn-primary mt-4 w-full !text-xs"
					>
						Coba di wizard →
					</a>
				</article>
			{/each}
		</div>
	{/if}

	<div class="mt-8">
		<Disclaimer variant="compact" />
	</div>
</div>
