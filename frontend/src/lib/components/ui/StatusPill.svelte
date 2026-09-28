<script lang="ts">
	import { health } from '$lib/stores/health.svelte';

	/**
	 * Indikator status koneksi backend. Ringkas, dengan tooltip berisi detail
	 * engine/LLM. Menampilkan "Memeriksa", "Terhubung", atau "Terputus".
	 */
	let { compact = false }: { compact?: boolean } = $props();

	const map = {
		unknown: { dot: 'bg-[var(--color-ink-faint)]', text: 'Memeriksa…', tone: 'ink-dim' },
		checking: { dot: 'bg-[var(--color-warn)] animate-pulse', text: 'Memeriksa…', tone: 'ink-dim' },
		online: { dot: 'bg-[var(--color-ok)]', text: 'Terhubung', tone: 'ok' },
		offline: { dot: 'bg-[var(--color-danger)]', text: 'Terputus', tone: 'danger' }
	} as const;

	let conf = $derived(map[health.state]);
	let detail = $derived(
		health.state === 'online' && health.info
			? `Engine ${health.info.engine_version} · asumsi ${health.info.assumption_set} · LLM ${health.info.llm_enabled ? 'aktif' : 'nonaktif'}`
			: health.state === 'offline'
				? 'Backend tidak dapat dijangkau. Coba lagi nanti.'
				: 'Memeriksa koneksi ke backend…'
	);
</script>

<button
	type="button"
	class="chip chip-activate !gap-1.5"
	title={detail}
	aria-label={`Status backend: ${conf.text}. ${detail}`}
	onclick={() => health.check()}
>
	<span class="inline-block h-2 w-2 shrink-0 rounded-full {conf.dot}" aria-hidden="true"></span>
	{#if !compact}
		<span class="text-[0.7rem]">{conf.text}</span>
	{/if}
</button>
