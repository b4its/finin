<script lang="ts">
	import Badge from '$lib/components/ui/Badge.svelte';
	import Tooltip from '$lib/components/ui/Tooltip.svelte';

	let {
		robust,
		reason,
		winners = {}
	}: { robust: boolean; reason: string; winners?: Record<string, string> } = $props();

	const presetLabels: Record<string, string> = {
		konservatif: 'Konservatif',
		moderat: 'Moderat',
		optimis: 'Optimis'
	};
</script>

<Tooltip
	text={robust
		? 'Pemenang sama di ketiga preset asumsi: ' +
			Object.entries(winners)
				.map(([k, v]) => `${presetLabels[k] ?? k} → ${v}`)
				.join(', ')
		: reason}
>
	<Badge level={robust ? 'ok' : 'orange'}>
		{robust ? '✓ Rekomendasi robust' : '⚠ Bergantung asumsi'}
	</Badge>
</Tooltip>
