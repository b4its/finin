<script lang="ts">
	import { page } from '$app/state';
	import { sim } from '$lib/stores/simulation.svelte';
	import StatusPill from '$lib/components/ui/StatusPill.svelte';

	let mobileOpen = $state(false);

	const path = $derived(page.url.pathname);
	const inSim = $derived(path.startsWith('/sim/'));
	const simId = $derived(inSim ? path.split('/')[2] : '');

	function isActive(href: string): boolean {
		return href === '/' ? path === '/' : path.startsWith(href);
	}

	function close() {
		mobileOpen = false;
	}

	// Tutup menu mobile saat rute berubah.
	$effect(() => {
		if (path) mobileOpen = false;
	});
</script>

<header
	class="no-print sticky top-0 z-40 border-b border-[var(--color-line-soft)] bg-[var(--color-void)]/80 backdrop-blur-lg"
>
	<div class="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4 sm:px-5">
		<div class="flex min-w-0 items-center gap-2">
			<a
				href="/"
				class="flex items-center gap-2 rounded-lg py-1.5 pr-2 font-bold transition hover:opacity-90"
				aria-label="Financial Twin — beranda"
			>
				<span class="text-lg" aria-hidden="true">🌌</span>
				<span class="text-sm sm:text-base">Financial Twin</span>
			</a>
			{#if inSim}
				<nav
					aria-label="Remah roti"
					class="hidden items-center gap-1.5 text-xs text-[var(--color-ink-dim)] sm:flex"
				>
					<span aria-hidden="true">/</span>
					<a href="/saya" class="rounded hover:text-[var(--color-ink)]"
						>Multiverse #{simId.slice(0, 8)}</a
					>
				</nav>
			{/if}
			<div class="hidden lg:block">
				<StatusPill compact />
			</div>
		</div>

		<nav class="hidden items-center gap-1.5 lg:flex" aria-label="Navigasi utama">
			<a
				href="/"
				class="rounded-lg px-3 py-1.5 text-xs font-medium transition {isActive('/') && path === '/'
					? 'bg-[var(--color-void-3)] text-[var(--color-ink)]'
					: 'text-[var(--color-ink-dim)] hover:bg-[var(--color-void-2)] hover:text-[var(--color-ink)]'}"
				aria-current={path === '/' ? 'page' : undefined}>Beranda</a
			>
			{#if sim.result}
				<a
					href={`/sim/${sim.result.id}`}
					class="rounded-lg px-3 py-1.5 text-xs font-medium transition {inSim
						? 'bg-[var(--color-void-3)] text-[var(--color-ink)]'
						: 'text-[var(--color-ink-dim)] hover:bg-[var(--color-void-2)] hover:text-[var(--color-ink)]'}"
					aria-current={inSim ? 'page' : undefined}>Simulasi aktif</a
				>
			{/if}
			<a
				href="/saya"
				class="rounded-lg px-3 py-1.5 text-xs font-medium transition {isActive('/saya')
					? 'bg-[var(--color-void-3)] text-[var(--color-ink)]'
					: 'text-[var(--color-ink-dim)] hover:bg-[var(--color-void-2)] hover:text-[var(--color-ink)]'}"
				aria-current={isActive('/saya') ? 'page' : undefined}>🗂️ Simulasi saya</a
			>
			<a
				href="/katalog"
				class="rounded-lg px-3 py-1.5 text-xs font-medium transition {isActive('/katalog')
					? 'bg-[var(--color-void-3)] text-[var(--color-ink)]'
					: 'text-[var(--color-ink-dim)] hover:bg-[var(--color-void-2)] hover:text-[var(--color-ink)]'}"
				aria-current={isActive('/katalog') ? 'page' : undefined}>🧩 Katalog</a
			>
			<a
				href="/bandingkan"
				class="rounded-lg px-3 py-1.5 text-xs font-medium transition {isActive('/bandingkan')
					? 'bg-[var(--color-void-3)] text-[var(--color-ink)]'
					: 'text-[var(--color-ink-dim)] hover:bg-[var(--color-void-2)] hover:text-[var(--color-ink)]'}"
				aria-current={isActive('/bandingkan') ? 'page' : undefined}>⚖️ Bandingkan</a
			>
			<a
				href="/start"
				class="btn btn-primary ml-1 !px-3.5 !py-1.5 !text-xs"
				aria-current={isActive('/start') ? 'page' : undefined}
			>
				+ Simulasi baru
			</a>
		</nav>

		<button
			class="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--color-line)] bg-[var(--color-panel-2)] text-[var(--color-ink-dim)] lg:hidden"
			aria-label={mobileOpen ? 'Tutup menu' : 'Buka menu navigasi'}
			aria-expanded={mobileOpen}
			aria-controls="mobile-nav"
			onclick={() => (mobileOpen = !mobileOpen)}
		>
			<span aria-hidden="true">{mobileOpen ? '✕' : '☰'}</span>
		</button>
	</div>

	{#if mobileOpen}
		<nav
			id="mobile-nav"
			class="border-t border-[var(--color-line-soft)] bg-[var(--color-void-1)] px-4 py-3 lg:hidden"
			aria-label="Navigasi seluler"
		>
			<ul class="space-y-1">
				<li>
					<a
						href="/"
						class="block rounded-lg px-3 py-2 text-sm {path === '/'
							? 'bg-[var(--color-void-3)] font-semibold text-[var(--color-ink)]'
							: 'text-[var(--color-ink-dim)]'}"
						onclick={close}>🌌 Beranda</a
					>
				</li>
				{#if sim.result}
					<li>
						<a
							href={`/sim/${sim.result.id}`}
							class="block rounded-lg px-3 py-2 text-sm {inSim
								? 'bg-[var(--color-void-3)] font-semibold text-[var(--color-ink)]'
								: 'text-[var(--color-ink-dim)]'}"
							onclick={close}>✨ Simulasi aktif</a
						>
					</li>
				{/if}
				<li>
					<a
						href="/saya"
						class="block rounded-lg px-3 py-2 text-sm {isActive('/saya')
							? 'bg-[var(--color-void-3)] font-semibold text-[var(--color-ink)]'
							: 'text-[var(--color-ink-dim)]'}"
						onclick={close}>🗂️ Simulasi saya</a
					>
				</li>
				<li>
					<a
						href="/katalog"
						class="block rounded-lg px-3 py-2 text-sm {isActive('/katalog')
							? 'bg-[var(--color-void-3)] font-semibold text-[var(--color-ink)]'
							: 'text-[var(--color-ink-dim)]'}"
						onclick={close}>🧩 Katalog keputusan</a
					>
				</li>
				<li>
					<a
						href="/bandingkan"
						class="block rounded-lg px-3 py-2 text-sm {isActive('/bandingkan')
							? 'bg-[var(--color-void-3)] font-semibold text-[var(--color-ink)]'
							: 'text-[var(--color-ink-dim)]'}"
						onclick={close}>⚖️ Bandingkan</a
					>
				</li>
				<li class="pt-1 border-t border-[var(--color-line-soft)]">
					<div class="flex items-center justify-between px-1 pt-2">
						<span class="text-xs text-[var(--color-ink-dim)]">Status backend</span>
						<StatusPill />
					</div>
				</li>
				<li class="pt-1">
					<a href="/start" class="btn btn-primary w-full" onclick={close}>+ Simulasi baru</a>
				</li>
			</ul>
		</nav>
	{/if}
</header>
