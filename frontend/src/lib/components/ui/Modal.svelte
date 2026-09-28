<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		open = $bindable(false),
		title = '',
		size = 'md',
		children
	}: {
		open: boolean;
		title?: string;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		children: Snippet;
	} = $props();

	const widths: Record<string, string> = {
		sm: 'max-w-md',
		md: 'max-w-2xl',
		lg: 'max-w-4xl',
		xl: 'max-w-6xl'
	};

	let dialog = $state<HTMLDivElement | null>(null);
	let lastFocused: HTMLElement | null = null;

	const FOCUSABLE =
		'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';

	function focusables(): HTMLElement[] {
		if (!dialog) return [];
		return Array.from(dialog.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
			(el) => el.offsetParent !== null || el === document.activeElement
		);
	}

	function onKey(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'Escape') {
			open = false;
			return;
		}
		if (e.key === 'Tab') {
			const els = focusables();
			if (els.length === 0) {
				e.preventDefault();
				return;
			}
			const first = els[0];
			const last = els[els.length - 1];
			const active = document.activeElement as HTMLElement | null;
			if (e.shiftKey && (active === first || !dialog?.contains(active))) {
				e.preventDefault();
				last.focus();
			} else if (!e.shiftKey && active === last) {
				e.preventDefault();
				first.focus();
			}
		}
	}

	// Kunci scroll body + kelola fokus saat modal dibuka/ditutup.
	$effect(() => {
		if (typeof document === 'undefined') return;
		if (open) {
			lastFocused = document.activeElement as HTMLElement | null;
			document.body.style.overflow = 'hidden';
			// Fokuskan elemen pertama setelah DOM stabil.
			queueMicrotask(() => {
				const els = focusables();
				(els[0] ?? dialog)?.focus();
			});
		} else {
			document.body.style.overflow = '';
			lastFocused?.focus?.();
		}
		return () => {
			document.body.style.overflow = '';
		};
	});
</script>

<svelte:window onkeydown={onKey} />

{#if open}
	<div
		class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 backdrop-blur-sm sm:items-center sm:p-4"
		onclick={(e) => e.target === e.currentTarget && (open = false)}
		role="presentation"
	>
		<div
			bind:this={dialog}
			class="card max-h-[88vh] w-full {widths[size] ??
				widths.md} overflow-y-auto p-5 shadow-[var(--shadow-float)] sm:p-6"
			role="dialog"
			aria-modal="true"
			aria-label={title}
			tabindex="-1"
		>
			<div class="mb-4 flex items-start justify-between gap-4">
				<h2 class="text-lg font-bold">{title}</h2>
				<button
					class="btn btn-ghost !px-2.5 !py-1.5"
					aria-label="Tutup dialog"
					onclick={() => (open = false)}>✕</button
				>
			</div>
			{@render children()}
		</div>
	</div>
{/if}
