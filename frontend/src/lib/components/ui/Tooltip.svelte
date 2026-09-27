<script lang="ts">
	import type { Snippet } from 'svelte';
	let { text, children }: { text: string | null | undefined; children: Snippet } = $props();
	let open = $state(false);
</script>

<span
	class="relative inline-flex"
	role="presentation"
	onmouseenter={() => (open = true)}
	onmouseleave={() => (open = false)}
	onfocusin={() => (open = true)}
	onfocusout={() => (open = false)}
>
	{@render children()}
	{#if open}
		<span
			role="tooltip"
			class="absolute bottom-full left-1/2 z-50 mb-2 w-60 -translate-x-1/2 rounded-lg border border-[var(--color-line)] bg-[var(--color-panel)] p-2.5 text-xs leading-relaxed text-[var(--color-ink)] shadow-xl"
		>
			{text}
		</span>
	{/if}
</span>
