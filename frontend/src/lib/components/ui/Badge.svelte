<script lang="ts">
	import type { Snippet } from 'svelte';
	let { level = 'neutral', children }: { level?: string; children: Snippet } = $props();

	const colors: Record<string, string> = {
		red: 'border-[var(--color-danger)] text-[var(--color-danger)] bg-red-500/10',
		orange: 'border-[var(--color-warn)] text-[var(--color-warn)] bg-amber-500/10',
		yellow: 'border-[var(--color-warn)] text-[var(--color-warn)] bg-amber-500/5',
		ok: 'border-[var(--color-ok)] text-[var(--color-ok)] bg-emerald-500/10',
		info: 'border-[var(--color-accent)] text-[var(--color-accent)] bg-blue-500/10',
		neutral: 'border-[var(--color-line)] text-[var(--color-ink-dim)]'
	};
</script>

<span class="chip {colors[level] ?? colors.neutral}">{@render children()}</span>
