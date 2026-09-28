<script lang="ts">
	import { onMount } from 'svelte';
	import { history } from '$lib/stores/history.svelte';
	import { toast } from '$lib/stores/toast.svelte';
	import { dateID } from '$lib/utils/format';
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';

	onMount(() => history.load());

	function remove(id: string) {
		history.remove(id);
		toast.info('Simulasi dihapus dari riwayat');
	}

	function clearAll() {
		if (confirm('Hapus seluruh riwayat simulasi lokal?')) {
			history.clear();
			toast.info('Riwayat simulasi dikosongkan');
		}
	}
</script>

<svelte:head><title>Simulasi saya — Financial Twin</title></svelte:head>

<div class="mx-auto max-w-3xl px-4 py-8 sm:px-5">
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div>
			<h1 class="text-2xl font-bold">🗂️ Simulasi saya</h1>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Riwayat tersimpan di perangkatmu saja (tanpa akun, tanpa server).
			</p>
		</div>
		{#if history.items.length}
			<button class="btn btn-ghost !py-1.5 !text-xs text-[var(--color-danger)]" onclick={clearAll}>
				Kosongkan
			</button>
		{/if}
	</div>

	<div class="mt-6 space-y-3">
		{#each history.items as r (r.id)}
			<div class="card card-interactive flex items-center justify-between gap-3 p-4">
				<a href={`/sim/${r.id}`} class="min-w-0 flex-1">
					<p class="truncate text-sm font-semibold">{r.label || `Simulasi ${r.id.slice(0, 8)}`}</p>
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
		{:else}
			<div class="card p-8 text-center">
				<p class="text-3xl" aria-hidden="true">🌌</p>
				<p class="mt-3 font-semibold">Belum ada simulasi tersimpan</p>
				<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
					Mulai simulasi pertamamu dan hasilnya akan tercatat di sini.
				</p>
				<a href="/start" class="btn btn-primary mt-5 !px-6 !py-2.5">Mulai simulasi →</a>
			</div>
		{/each}
	</div>

	<div class="mt-8">
		<Disclaimer variant="compact" />
	</div>
</div>
