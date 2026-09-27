<script lang="ts">
	import { rupiah } from '$lib/utils/format';

	let {
		value = $bindable(0),
		label = '',
		help = '',
		placeholder = '0'
	}: {
		value: number;
		label?: string;
		help?: string;
		placeholder?: string;
	} = $props();

	const shortcuts = [0, 1_000_000, 2_500_000, 5_000_000, 10_000_000, 25_000_000];

	function onInput(e: Event) {
		const raw = (e.target as HTMLInputElement).value.replace(/[^\d]/g, '');
		value = raw ? parseInt(raw, 10) : 0;
	}
</script>

<label class="block">
	{#if label}
		<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]">{label}</span>
	{/if}
	<div class="relative">
		<span
			class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[var(--color-ink-dim)]"
			>Rp</span
		>
		<input
			class="input num pl-9"
			type="text"
			inputmode="numeric"
			{placeholder}
			value={value ? value.toLocaleString('id-ID') : ''}
			oninput={onInput}
		/>
	</div>
	<div class="mt-2 flex flex-wrap gap-1.5">
		{#each shortcuts as s}
			<button
				type="button"
				class="chip hover:border-[var(--color-accent)]"
				class:active={value === s}
				onclick={() => (value = s)}
			>
				{s === 0 ? 'Kosong' : rupiah(s).replace('Rp', 'Rp ')}
			</button>
		{/each}
	</div>
	{#if help}
		<p class="mt-1.5 text-xs text-[var(--color-ink-dim)]">{help}</p>
	{/if}
</label>
