<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
</script>

<header
	class="no-print sticky top-0 z-40 border-b border-[var(--color-line-soft)] bg-[var(--color-void)]/80 backdrop-blur-lg"
>
	<div class="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4 sm:px-5">
		<a
			href="/"
			class="flex items-center gap-2 rounded-lg py-1.5 pr-2 font-bold transition hover:opacity-90"
			aria-label="Financial Twin — beranda"
		>
			<span class="text-lg" aria-hidden="true">🌌</span>
			<span class="text-sm sm:text-base">Financial Twin</span>
		</a>

		<nav class="flex items-center gap-1.5" aria-label="Navigasi utama">
			<a
				href="/start"
				class="btn btn-primary !px-3.5 !py-1.5 !text-xs sm:!px-5 sm:!py-2 sm:!text-sm"
				aria-current={$page.url.pathname === '/start' ? 'page' : undefined}
			>
				Mulai simulasi
			</a>
			<button
				class="hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-panel-2)] px-2.5 py-1.5 text-xs text-[var(--color-ink-dim)] transition hover:text-[var(--color-ink)] sm:inline-flex sm:items-center sm:gap-1.5"
				aria-label="Buka riwayat simulasi saya"
				onclick={() => goto('/saya')}
			>
				<span aria-hidden="true">🗂️</span> Simulasi saya
			</button>
		</nav>
	</div>
</header>
