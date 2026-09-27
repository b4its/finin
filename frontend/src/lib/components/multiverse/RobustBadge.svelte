<script lang="ts">
	import Badge from '$lib/components/ui/Badge.svelte';
	import Tooltip from '$lib/components/ui/Tooltip.svelte';

	let {
		robust,
		reason,
		winners = {},
		drivers = []
	}: {
		robust: boolean;
		reason: string;
		winners?: Record<string, string>;
		drivers?: string[];
	} = $props();

	const presetLabels: Record<string, string> = {
		konservatif: 'Konservatif',
		moderat: 'Moderat',
		optimis: 'Optimis'
	};

	let tooltip = $derived.by(() => {
		if (robust) {
			const list = Object.entries(winners)
				.map(([k, v]) => `${presetLabels[k] ?? k} → ${v}`)
				.join(', ');
			return `Pemenang sama di ketiga preset asumsi: ${list}`;
		}
		const parts = [reason];
		if (drivers.length) parts.push(`Parameter pemicu: ${drivers.join(', ')}.`);
		return parts.join(' ');
	});
</script>

<Tooltip text={tooltip}>
	<button
		type="button"
		class="cursor-help"
		aria-label={`Status rekomendasi: ${robust ? 'robust' : 'bergantung asumsi'}`}
	>
		<Badge level={robust ? 'ok' : 'orange'}>
			{robust ? '✓ Rekomendasi robust' : '⚠ Bergantung asumsi'}
		</Badge>
	</button>
</Tooltip>
