<script lang="ts">
	import type { Snippet } from 'svelte';

	/**
	 * Dropdown aksesibel: menutup saat Escape, klik di luar, atau memilih item.
	 * Menggantikan pola menu kustom yang sebelumnya tidak bisa ditutup tanpa memilih.
	 */
	let {
		label,
		title = '',
		align = 'right',
		buttonClass = 'btn btn-ghost !py-1.5 !px-3 text-xs',
		children
	}: {
		label: string;
		title?: string;
		align?: 'left' | 'right';
		buttonClass?: string;
		children: Snippet;
	} = $props();

	let open = $state(false);
	let root = $state<HTMLDivElement | null>(null);

	function toggle() {
		open = !open;
	}

	function close() {
		open = false;
	}

	function onWindowPointer(e: PointerEvent) {
		if (!open) return;
		if (!root?.contains(e.target as Node)) {
			close();
			return;
		}
		if ((e.target as Element).closest('a, [data-dropdown-item]')) {
			// Tutup pada macrotask berikutnya, BUKAN microtask: `pointerdown`
			// mendahului rangkaian pointerup/click, dan microtask terkuras lebih
			// dulu sehingga elemen <a> terlepas dari DOM sebelum `click` dikirim —
			// tautan unduh (CSV/JSON) jadi tak pernah terpicu. setTimeout(…, 0)
			// memberi kesempatan event click selesai dulu.
			setTimeout(close, 0);
		}
	}

	function onKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && open) {
			close();
			(root?.querySelector('button[aria-expanded]') as HTMLButtonElement | null)?.focus();
		}
	}
</script>

<svelte:window onpointerdown={onWindowPointer} onkeydown={onKeydown} />

<div class="relative inline-block" bind:this={root}>
	<button type="button" class={buttonClass} {title} aria-expanded={open} onclick={toggle}>
		{label}
	</button>
	{#if open}
		<div
			class="absolute top-full z-20 mt-1 w-52 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-1)] p-1.5 text-left shadow-xl {align ===
			'right'
				? 'right-0'
				: 'left-0'}"
		>
			{@render children()}
		</div>
	{/if}
</div>
