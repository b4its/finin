<script lang="ts">
	import '../app.css';
	import AppHeader from '$lib/components/ui/AppHeader.svelte';
	import AppFooter from '$lib/components/ui/AppFooter.svelte';
	import Toaster from '$lib/components/ui/Toaster.svelte';
	import BackToTop from '$lib/components/ui/BackToTop.svelte';
	import { onMount } from 'svelte';
	import { history } from '$lib/stores/history.svelte';
	import { health } from '$lib/stores/health.svelte';

	let { children } = $props();

	onMount(() => {
		history.load();
		health.start();
		return () => health.stop();
	});
</script>

<a
	href="#main"
	class="sr-only-focusable fixed left-3 top-3 z-[110] rounded-lg border border-[var(--color-accent)] bg-[var(--color-panel)] px-4 py-2 text-sm font-semibold text-[var(--color-ink)] shadow-lg"
>
	Lompat ke konten utama
</a>

<AppHeader />

<main id="main" tabindex="-1">
	{@render children()}
</main>

<AppFooter />
<BackToTop />
<Toaster />
