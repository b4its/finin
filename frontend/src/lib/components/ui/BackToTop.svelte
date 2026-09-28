<script lang="ts">
	/** Tombol "kembali ke atas" yang muncul setelah pengguna menggulir cukup jauh. */

	let visible = $state(false);

	function onScroll() {
		visible = window.scrollY > 600;
	}

	function toTop() {
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}
</script>

<svelte:window onscroll={onScroll} />

{#if visible}
	<button
		type="button"
		class="no-print fixed bottom-5 right-5 z-40 flex h-11 w-11 items-center justify-center rounded-full border border-[var(--color-line)] bg-[var(--color-panel)] text-lg text-[var(--color-ink)] shadow-[var(--shadow-float)] transition hover:-translate-y-0.5 hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
		aria-label="Kembali ke atas"
		title="Kembali ke atas"
		onclick={toTop}
	>
		<span aria-hidden="true">↑</span>
	</button>
{/if}
