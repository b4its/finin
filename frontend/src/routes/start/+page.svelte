<script lang="ts">
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';
	import FutureSelfScale from '$lib/components/ui/FutureSelfScale.svelte';
	import StepIncome from '$lib/components/wizard/StepIncome.svelte';
	import StepPosition from '$lib/components/wizard/StepPosition.svelte';
	import StepDecision from '$lib/components/wizard/StepDecision.svelte';
	import StepAssumption from '$lib/components/wizard/StepAssumption.svelte';
	import { sim } from '$lib/stores/simulation.svelte';
	import { toast } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let step = $state(0);
	let fsc = $state<number | null>(sim.fscPre);
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
			toast.success(`Multiverse dibangun: ${res.twins.length} cabang siap dijelajahi.`);
			await goto(`/sim/${res.id}`);
		} catch (e) {
			buildError = String(e);
			toast.error('Gagal membangun multiverse. Cek koneksi backend lalu coba lagi.');
		} finally {
			building = false;
		}
	}
</script>

<svelte:head><title>Mulai — Financial Twin</title></svelte:head>

<div class="mx-auto max-w-3xl px-4 py-6 sm:px-5 sm:py-8">
	<div class="mb-6 flex items-center justify-between gap-3">
		<div>
			<h1 class="text-lg font-bold">Bangun multiverse-mu</h1>
			<p class="text-xs text-[var(--color-ink-dim)]">Selesai dalam &lt; 90 detik · tanpa akun</p>
		</div>
		<div class="flex gap-1" aria-label={`Progres: langkah ${step + 1} dari 4`} role="img">
			{#each steps as _s, i}
				<span
					class="h-1.5 w-8 rounded-full transition-colors"
					class:bg-[var(--color-accent)]={i <= step}
					class:bg-[var(--color-line)]={i > step}
				></span>
			{/each}
		</div>
	</div>

	{#if step === 0 && fsc === null}
		<div class="card mb-4 p-5">
			<div class="flex items-center justify-between">
				<h2 class="text-base font-bold">
					🧬 Sebelum mulai — seberapa dekat kamu dengan masa depan?
				</h2>
				<button
					class="text-xs text-[var(--color-ink-dim)] hover:underline"
					onclick={() => (fsc = 0)}
				>
					Lewati
				</button>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Riset Hershfield (2011) membuktikan: keterhubungan visual dengan diri masa depan
				melipatgandakan tabungan.
			</p>
			<div class="mt-3">
				<FutureSelfScale bind:value={fsc} compact />
			</div>
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
