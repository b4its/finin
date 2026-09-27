<script lang="ts">
	import type { Snippet } from 'svelte';
	let {
		open = $bindable(false),
		title = '',
		children
	}: { open: boolean; title?: string; children: Snippet } = $props();

	function onKey(e: KeyboardEvent) {
		if (e.key === 'Escape') open = false;
	}
</script>

<svelte:window onkeydown={onKey} />

{#if open}
	<div
		class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 backdrop-blur-sm sm:items-center sm:p-4"
		onclick={(e) => e.target === e.currentTarget && (open = false)}
		role="presentation"
	>
		<div
			class="card max-h-[88vh] w-full max-w-2xl overflow-y-auto p-5 sm:p-6"
			role="dialog"
			aria-modal="true"
			aria-label={title}
		>
			<div class="mb-4 flex items-start justify-between gap-4">
				<h2 class="text-lg font-bold">{title}</h2>
				<button
					class="btn btn-ghost !px-2.5 !py-1.5"
					aria-label="Tutup"
					onclick={() => (open = false)}>✕</button
				>
			</div>
			{@render children()}
		</div>
	</div>
{/if}
