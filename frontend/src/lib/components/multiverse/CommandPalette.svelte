<script lang="ts">
	import { goto } from '$app/navigation';
	import { toast } from '$lib/stores/toast.svelte';
	import type { Twin } from '$lib/api/types';

	interface Item {
		id: string;
		label: string;
		icon: string;
		hint?: string;
		run: () => void;
	}

	let {
		tabs,
		twins,
		simulationId = '',
		onSelectTab,
		onSelectTwin,
		onOpenReport,
		onOpenPitch,
		onOpenShare
	}: {
		tabs: readonly { id: string; label: string; icon: string }[];
		twins: Twin[];
		simulationId?: string;
		onSelectTab: (id: string) => void;
		onSelectTwin: (code: string) => void;
		onOpenReport: () => void;
		onOpenPitch: () => void;
		onOpenShare: () => void;
	} = $props();

	let open = $state(false);
	let query = $state('');
	let active = $state(0);
	let inputEl = $state<HTMLInputElement | null>(null);

	const commands = $derived.by<Item[]>(() => [
		...tabs.map((t) => ({
			id: `tab:${t.id}`,
			label: t.label,
			icon: t.icon,
			hint: 'Modul',
			run: () => onSelectTab(t.id)
		})),
		...twins.map((t) => ({
			id: `twin:${t.code}`,
			label: `Twin ${t.code} — ${t.label}`,
			icon: t.icon || '●',
			hint: 'Detail twin',
			run: () => onSelectTwin(t.code)
		})),
		{ id: 'act:report', label: 'Cetak laporan PDF', icon: '📄', hint: 'Aksi', run: onOpenReport },
		{ id: 'act:pitch', label: 'Mulai presentasi juri', icon: '⚡', hint: 'Aksi', run: onOpenPitch },
		{ id: 'act:share', label: 'Bagikan hasil', icon: '✨', hint: 'Aksi', run: onOpenShare },
		{
			id: 'nav:compare',
			label: 'Bandingkan dengan simulasi lain',
			icon: '⚖️',
			hint: 'Navigasi',
			run: () => void goto(simulationId ? `/bandingkan?ids=${simulationId}` : '/bandingkan')
		},
		{
			id: 'nav:catalog',
			label: 'Buka katalog keputusan',
			icon: '🧩',
			hint: 'Navigasi',
			run: () => void goto('/katalog')
		},
		{
			id: 'nav:new',
			label: 'Mulai simulasi baru',
			icon: '➕',
			hint: 'Navigasi',
			run: () => void goto('/start')
		},
		{
			id: 'nav:history',
			label: 'Riwayat simulasi saya',
			icon: '🗂️',
			hint: 'Navigasi',
			run: () => void goto('/saya')
		},
		{
			id: 'act:copy',
			label: 'Salin link simulasi ini',
			icon: '🔗',
			hint: 'Aksi',
			run: () => void copyLink()
		}
	]);

	async function copyLink() {
		try {
			await navigator.clipboard.writeText(window.location.href);
			toast.success('Link simulasi disalin ke clipboard');
		} catch {
			toast.error('Gagal menyalin link — salin manual dari address bar');
		}
	}

	const filtered = $derived.by(() => {
		const q = query.trim().toLowerCase();
		if (!q) return commands;
		return commands.filter(
			(c) => c.label.toLowerCase().includes(q) || (c.hint ?? '').toLowerCase().includes(q)
		);
	});

	function toggle() {
		open = !open;
		if (open) {
			query = '';
			active = 0;
			queueMicrotask(() => inputEl?.focus());
		}
	}

	function runItem(item: Item | undefined) {
		if (!item) return;
		open = false;
		item.run();
	}

	function onKey(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
			e.preventDefault();
			toggle();
			return;
		}
		if (!open) return;
		if (e.key === 'Escape') {
			open = false;
		} else if (e.key === 'ArrowDown') {
			e.preventDefault();
			active = Math.min(active + 1, filtered.length - 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			active = Math.max(active - 1, 0);
		} else if (e.key === 'Enter') {
			e.preventDefault();
			runItem(filtered[active]);
		}
	}
</script>

<svelte:window onkeydown={onKey} />

<button
	class="btn btn-ghost !px-3 !py-1.5 !text-xs"
	onclick={toggle}
	aria-label="Buka palet perintah (Ctrl+K)"
	title="Cari modul, twin, atau aksi (Ctrl+K)"
>
	<span aria-hidden="true">⌘</span> <span class="hidden sm:inline">Cari modul</span>
	<kbd
		class="ml-1 hidden rounded border border-[var(--color-line)] bg-[var(--color-void-2)] px-1.5 py-0.5 text-[10px] text-[var(--color-ink-dim)] sm:inline"
		>Ctrl K</kbd
	>
</button>

{#if open}
	<div
		class="fixed inset-0 z-[90] flex items-start justify-center bg-black/60 p-4 pt-[12vh] backdrop-blur-sm"
		onclick={(e) => e.target === e.currentTarget && (open = false)}
		role="presentation"
	>
		<div
			class="card w-full max-w-lg overflow-hidden p-0 shadow-[var(--shadow-float)]"
			role="dialog"
			aria-modal="true"
			aria-label="Palet perintah"
		>
			<div class="flex items-center gap-2 border-b border-[var(--color-line)] px-4 py-3">
				<span aria-hidden="true">🔍</span>
				<input
					bind:this={inputEl}
					bind:value={query}
					class="w-full bg-transparent text-sm text-[var(--color-ink)] outline-none placeholder:text-[var(--color-ink-faint)]"
					placeholder="Cari modul, twin, atau aksi…"
					aria-label="Cari perintah"
					role="combobox"
					aria-expanded="true"
					aria-controls="cmdk-list"
				/>
				<kbd class="rounded border border-[var(--color-line)] px-1.5 py-0.5 text-[10px]">Esc</kbd>
			</div>
			<ul id="cmdk-list" class="max-h-80 overflow-y-auto p-1.5" role="listbox">
				{#each filtered as item, i (item.id)}
					<li role="option" aria-selected={i === active}>
						<button
							class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition {i ===
							active
								? 'bg-[var(--color-accent)]/15 text-[var(--color-ink)]'
								: 'text-[var(--color-ink-dim)] hover:bg-[var(--color-void-3)]'}"
							onmouseenter={() => (active = i)}
							onclick={() => runItem(item)}
						>
							<span aria-hidden="true">{item.icon}</span>
							<span class="flex-1 truncate">{item.label}</span>
							{#if item.hint}<span class="text-[10px] text-[var(--color-ink-faint)]"
									>{item.hint}</span
								>{/if}
						</button>
					</li>
				{:else}
					<li class="px-3 py-6 text-center text-sm text-[var(--color-ink-dim)]">
						Tidak ada hasil untuk "{query}"
					</li>
				{/each}
			</ul>
		</div>
	</div>
{/if}
