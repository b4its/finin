<script lang="ts">
	let {
		value = $bindable(0),
		label = '',
		suffix = '%',
		step = 0.01,
		min = 0,
		max = 100,
		help = ''
	}: {
		value: number;
		label?: string;
		suffix?: string;
		step?: number;
		min?: number;
		max?: number;
		help?: string;
	} = $props();

	function onInput(e: Event) {
		const v = parseFloat((e.target as HTMLInputElement).value.replace(',', '.'));
		value = isNaN(v) ? 0 : v / 100;
	}

	/**
	 * Tampilkan persen tanpa noise floating-point.
	 * `0.068 * 100` = `6.800000000000001` yang akan tampil literal di input
	 * `type="number"`; bulatkan ke presisi wajar agar bersih ("6.8").
	 */
	let displayValue = $derived(Number((value * 100).toPrecision(12)).toString());
</script>

<label class="block">
	{#if label}
		<span class="mb-1.5 block text-sm font-medium text-[var(--color-ink-dim)]">{label}</span>
	{/if}
	<div class="relative">
		<input
			class="input num pr-10"
			type="number"
			{min}
			{max}
			{step}
			value={displayValue}
			oninput={onInput}
		/>
		<span
			class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-[var(--color-ink-dim)]"
			>{suffix}</span
		>
	</div>
	{#if help}
		<p class="mt-1.5 text-xs text-[var(--color-ink-dim)]">{help}</p>
	{/if}
</label>
