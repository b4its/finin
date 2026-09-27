<script lang="ts">
	let { checked = $bindable(false), label = '' }: { checked: boolean; label?: string } = $props();
</script>

<label class="flex cursor-pointer items-center gap-3">
	<button
		type="button"
		role="switch"
		aria-checked={checked}
		aria-label={label || 'Toggle'}
		class="relative h-6 w-11 rounded-full transition-colors"
		class:bg-[var(--color-accent)]={checked}
		class:bg-[var(--color-line)]={!checked}
		onclick={() => (checked = !checked)}
	>
		<span
			class="absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all"
			class:left-[1.375rem]={checked}
			class:left-0.5={!checked}
		></span>
	</button>
	{#if label}<span class="text-sm">{label}</span>{/if}
</label>
