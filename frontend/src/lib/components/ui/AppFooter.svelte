<script lang="ts">
	import { page } from '$app/stores';

	let year = new Date().getFullYear();
	let path = $derived($page.url.pathname);

	const links = [
		{ href: '/', label: 'Beranda' },
		{ href: '/start', label: 'Mulai simulasi' },
		{ href: '/saya', label: 'Simulasi saya' }
	];

	const sources = [
		{ href: 'https://www.ojk.go.id', label: 'OJK' },
		{ href: 'https://www.bi.go.id', label: 'Bank Indonesia' },
		{ href: 'https://www.bps.go.id', label: 'BPS' },
		{ href: 'https://www.lps.go.id', label: 'LPS' }
	];
</script>

<footer class="no-print mt-16 border-t border-[var(--color-line-soft)]">
	<div class="mx-auto max-w-6xl px-4 py-8 sm:px-5">
		<div class="grid grid-cols-1 gap-8 sm:grid-cols-3">
			<div>
				<div class="flex items-center gap-2 font-bold">
					<span aria-hidden="true">🌌</span>
					<span>Financial Twin</span>
				</div>
				<p class="mt-2 max-w-xs text-xs leading-relaxed text-[var(--color-ink-dim)]">
					Decision-support system yang membuat "kembaran digital" finansialmu. Angka dihitung engine
					deterministik; AI hanya menarasikan.
				</p>
			</div>

			<nav aria-label="Navigasi footer">
				<h2 class="text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
					Navigasi
				</h2>
				<ul class="mt-3 space-y-2">
					{#each links as l}
						<li>
							<a
								href={l.href}
								class="text-sm text-[var(--color-ink-dim)] transition hover:text-[var(--color-ink)]"
								aria-current={path === l.href ? 'page' : undefined}>{l.label}</a
							>
						</li>
					{/each}
				</ul>
			</nav>

			<div>
				<h2 class="text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
					Sumber data
				</h2>
				<ul class="mt-3 flex flex-wrap gap-x-4 gap-y-2">
					{#each sources as s}
						<li>
							<a
								href={s.href}
								target="_blank"
								rel="noreferrer"
								class="text-sm text-[var(--color-ink-dim)] underline-offset-2 transition hover:text-[var(--color-accent)] hover:underline"
								>{s.label} ↗</a
							>
						</li>
					{/each}
				</ul>
				<p class="mt-3 text-xs text-[var(--color-ink-faint)]">
					Set asumsi berversi · data per Sep 2026
				</p>
			</div>
		</div>

		<div
			class="mt-8 flex flex-col items-start justify-between gap-3 border-t border-[var(--color-line-soft)] pt-5 text-xs text-[var(--color-ink-faint)] sm:flex-row sm:items-center"
		>
			<p>© {year} Financial Twin · Projek edukasi finansial.</p>
			<p>Tanpa akun · tanpa NIK · simulasi anonim &amp; retensi 30 hari (UU 27/2022 PDP).</p>
		</div>
	</div>
</footer>
