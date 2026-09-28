<script lang="ts">
	import { toast, type ToastKind } from '$lib/stores/toast.svelte';

	const meta: Record<ToastKind, { icon: string; border: string; text: string; bg: string }> = {
		success: {
			icon: '✓',
			border: 'border-[var(--color-ok)]',
			text: 'text-[var(--color-ok)]',
			bg: 'bg-emerald-500/10'
		},
		error: {
			icon: '✕',
			border: 'border-[var(--color-danger)]',
			text: 'text-[var(--color-danger)]',
			bg: 'bg-red-500/10'
		},
		info: {
			icon: 'ℹ',
			border: 'border-[var(--color-accent)]',
			text: 'text-[var(--color-accent)]',
			bg: 'bg-blue-500/10'
		},
		warn: {
			icon: '⚠',
			border: 'border-[var(--color-warn)]',
			text: 'text-[var(--color-warn)]',
			bg: 'bg-amber-500/10'
		}
	};
</script>

<div
	class="pointer-events-none fixed inset-x-0 bottom-0 z-[100] flex flex-col items-center gap-2 p-4 sm:items-end sm:p-6"
	aria-live="polite"
	aria-atomic="false"
>
	{#each toast.items as t (t.id)}
		{@const m = meta[t.kind]}
		<div
			class="pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl border bg-[var(--color-panel)] p-3 shadow-[var(--shadow-float)] {m.border}"
			role="status"
		>
			<span
				class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold {m.bg} {m.text}"
				aria-hidden="true">{m.icon}</span
			>
			<p class="flex-1 text-sm leading-snug text-[var(--color-ink)]">{t.message}</p>
			<button
				class="-mr-1 -mt-1 rounded-lg p-1 text-[var(--color-ink-dim)] transition hover:bg-[var(--color-void-3)] hover:text-[var(--color-ink)]"
				aria-label="Tutup notifikasi"
				onclick={() => toast.dismiss(t.id)}>✕</button
			>
		</div>
	{/each}
</div>
