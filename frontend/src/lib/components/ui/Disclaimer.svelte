<script lang="ts">
	let { variant = 'full' }: { variant?: 'full' | 'compact' } = $props();
</script>

{#if variant === 'compact'}
	<p class="text-xs leading-relaxed text-[var(--color-ink-dim)]">
		⚠️ Alat simulasi edukatif, bukan nasihat keuangan. Proyeksi bergantung asumsi dan tidak menjamin
		hasil.
	</p>
{:else}
	<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4">
		<p class="text-xs leading-relaxed text-[var(--color-ink-dim)]">
			<strong class="text-[var(--color-ink)]">Disclaimer.</strong>
			Financial Twin adalah alat simulasi edukatif, bukan nasihat keuangan, investasi, atau hukum. Proyeksi
			bergantung pada asumsi dan tidak menjamin hasil. Konsultasikan keputusan penting dengan perencana
			keuangan berlisensi.
		</p>
	</div>
{/if}
