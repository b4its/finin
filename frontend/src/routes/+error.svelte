<script lang="ts">
	import { page } from '$app/state';

	let { error } = $props<{ error?: { message?: string; status?: number } }>();
	const status = $derived(error?.status ?? 500);
	const isNotFound = $derived(status === 404);
	const currentPath = $derived(page.url.pathname);
</script>

<svelte:head
	><title>{isNotFound ? '404 — ' : 'Terjadi kesalahan — '}Financial Twin</title></svelte:head
>

<div class="mx-auto flex max-w-lg flex-col items-center px-4 py-20 text-center">
	<p class="text-6xl" aria-hidden="true">{isNotFound ? '🛰️' : '⚠️'}</p>
	<h1 class="mt-4 text-2xl font-bold">
		{isNotFound ? 'Halaman tidak ditemukan' : 'Terjadi kesalahan'}
	</h1>
	<p class="mt-2 text-sm text-[var(--color-ink-dim)]">
		{isNotFound
			? `Kami tidak menemukan ${currentPath}. Mungkin tautannya salah atau simulasi sudah kedaluwarsa.`
			: (error?.message ?? 'Sesuatu yang tidak terduga terjadi.')}
	</p>
	<div class="mt-6 flex flex-wrap justify-center gap-2">
		<a href="/" class="btn btn-primary">Ke beranda</a>
		<a href="/start" class="btn btn-ghost">Mulai simulasi</a>
		<a href="/katalog" class="btn btn-ghost">Katalog keputusan</a>
		<a href="/saya" class="btn btn-ghost">Riwayat simulasi</a>
	</div>
</div>
