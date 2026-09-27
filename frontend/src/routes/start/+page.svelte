<script lang="ts">
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';
	import StepIncome from '$lib/components/wizard/StepIncome.svelte';
	import StepPosition from '$lib/components/wizard/StepPosition.svelte';
	import StepDecision from '$lib/components/wizard/StepDecision.svelte';
	import StepAssumption from '$lib/components/wizard/StepAssumption.svelte';
	import { sim } from '$lib/stores/simulation.svelte';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let step = $state(0);
	let fsc = $state<number | null>(null);
	let building = $state(false);
	let buildError = $state<string | null>(null);

	const steps = ['Penghasilan', 'Posisi', 'Keputusan', 'Asumsi'];

	onMount(() => {
		sim.loadAssumptions();
	});

	let canNext = $derived(
		step === 0
			? sim.input.profile.income_monthly >= 0
			: step === 2
				? sim.input.decisions.length >= 1
				: true
	);

	async function next() {
		if (step < 3) {
			step++;
			return;
		}
		await run();
	}

	function back() {
		if (step > 0) step--;
	}

	async function run() {
		if (fsc !== null) {
			// dicatat setelah simulasi dibuat (butuh id), disimpan sementara
			sessionStorage.setItem('fsc_pre', String(fsc));
		}
		building = true;
		buildError = null;
		try {
			const res = await sim.simulate();
			const pre = sessionStorage.getItem('fsc_pre');
			if (pre && res) {
				const { api } = await import('$lib/api/client');
				await api.recordEvent(res.id, 'fsc_pre', parseInt(pre)).catch(() => {});
				sessionStorage.removeItem('fsc_pre');
			}
			await goto(`/sim/${res.id}`);
		} catch (e) {
			buildError = String(e);
		} finally {
			building = false;
		}
	}
</script>

<svelte:head><title>Mulai — Financial Twin</title></svelte:head>

<div class="mx-auto max-w-3xl px-5 py-8">
	<header class="mb-6 flex items-center justify-between">
		<a href="/" class="flex items-center gap-2 font-bold">
			<span>🌌</span> Financial Twin
		</a>
		<div class="flex gap-1">
			{#each steps as _s, i}
				<span
					class="h-1.5 w-8 rounded-full"
					class:bg-[var(--color-accent)]={i <= step}
					class:bg-[var(--color-line)]={i > step}
				></span>
			{/each}
		</div>
	</header>

	{#if step === 0 && fsc === null}
		<div class="card mb-4 p-5">
			<h2 class="text-lg font-bold">Sebelum mulai — satu pertanyaan singkat</h2>
			<p class="mt-1 text-sm text-[var(--color-ink-dim)]">
				Seberapa dekat kamu merasa dengan “dirimu di masa depan”? (opsional, 1–7)
			</p>
			<div class="mt-3 flex flex-wrap gap-1.5">
				{#each [1, 2, 3, 4, 5, 6, 7] as v}
					<button class="chip flex-col !px-3 !py-2" onclick={() => (fsc = v)}>
						<span class="num text-base font-bold">{v}</span>
					</button>
				{/each}
			</div>
			<div class="mt-2 flex justify-between text-xs text-[var(--color-ink-dim)]">
				<span>orang asing</span><span>aku sendiri</span>
			</div>
			<button class="mt-3 text-xs text-[var(--color-accent)] underline" onclick={() => (fsc = 0)}>
				Lewati saja
			</button>
		</div>
	{/if}

	<div class="card p-5 sm:p-6">
		<div class="mb-5">
			<div class="text-xs text-[var(--color-ink-dim)]">Langkah {step + 1} dari 4</div>
			<div class="text-sm font-semibold">{steps[step]}</div>
		</div>

		{#if step === 0}
			<StepIncome />
		{:else if step === 1}
			<StepPosition />
		{:else if step === 2}
			<StepDecision />
		{:else}
			<StepAssumption />
		{/if}
	</div>

	{#if buildError}
		<div class="mt-4 rounded-xl border border-[var(--color-danger)] bg-red-500/10 p-3 text-sm">
			{buildError}
		</div>
	{/if}

	<div class="mt-5 flex items-center justify-between">
		<button class="btn btn-ghost" onclick={back} disabled={step === 0}>← Kembali</button>
		<button class="btn btn-primary" onclick={next} disabled={!canNext || building}>
			{#if building}
				Membangun multiverse…
			{:else if step === 3}
				Bangun multiverse →
			{:else}
				Lanjut →
			{/if}
		</button>
	</div>

	{#if building}
		<div
			class="mt-4 flex items-center gap-3 rounded-xl border border-[var(--color-accent)] bg-blue-500/5 p-4"
		>
			<span class="animate-pulse text-xl">✨</span>
			<p class="text-sm">
				Membuat 3–5 kembaran digitalmu, menghitung 240 bulan × 3 preset, dan mengecek aturan OJK…
			</p>
		</div>
	{/if}

	<div class="mt-8">
		<Disclaimer variant="compact" />
	</div>
</div>
