<script lang="ts">
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';
	import FutureSelfScale from '$lib/components/ui/FutureSelfScale.svelte';
	import StepIncome from '$lib/components/wizard/StepIncome.svelte';
	import StepPosition from '$lib/components/wizard/StepPosition.svelte';
	import StepDecision from '$lib/components/wizard/StepDecision.svelte';
	import StepAssumption from '$lib/components/wizard/StepAssumption.svelte';
	import StepReview from '$lib/components/wizard/StepReview.svelte';
	import { sim } from '$lib/stores/simulation.svelte';
	import { toast } from '$lib/stores/toast.svelte';
	import { validateStep, type WizardStep, type WizardUiStep } from '$lib/utils/wizard-validation';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';

	const LAST_STEP = 4; // 0..4 (4 = review)
	let step = $state<WizardUiStep>(0);
	let fsc = $state<number | null>(sim.fscPre);
	let fscSkipped = $state(false);
	let building = $state(false);
	let buildError = $state<string | null>(null);

	/** Template yang diminta dari katalog (`/start?template=<type>`) — diteruskan ke langkah keputusan. */
	let preselectTemplate = $derived(page.url.searchParams.get('template') ?? '');
	let preselected = $state(false);

	const steps = ['Penghasilan', 'Posisi', 'Keputusan', 'Asumsi', 'Ringkasan'];

	onMount(() => {
		sim.loadAssumptions();
		// Bila datang dari katalog dengan template tertentu, lompat ke langkah keputusan.
		if (preselectTemplate) {
			step = 2;
			preselected = true;
		}
	});

	/** Validasi langkah saat ini (review = langkah terakhir, selalu lolos). */
	let currentValidation = $derived(
		step <= 3 ? validateStep(step as WizardStep, sim.input) : { valid: true, issues: [] }
	);
	let canNext = $derived(currentValidation.valid);

	async function next() {
		if (!canNext) return;
		if (step < LAST_STEP) {
			step = (step + 1) as WizardUiStep;
			scrollTop();
			return;
		}
		await run();
	}

	function back() {
		if (step > 0) {
			step = (step - 1) as WizardUiStep;
			scrollTop();
		}
	}

	function gotoStep(s: WizardUiStep) {
		step = s;
		scrollTop();
	}

	/** Reset penuh: hapus isian, draf tersimpan, dan kembali ke langkah pertama. */
	let confirmReset = $state(false);

	function resetAll() {
		if (!confirmReset) {
			confirmReset = true;
			setTimeout(() => (confirmReset = false), 4000);
			return;
		}
		confirmReset = false;
		sim.reset();
		fsc = null;
		fscSkipped = false;
		preselected = false;
		step = 0;
		toast.info('Isian wizard direset');
		scrollTop();
	}

	function scrollTop() {
		document.getElementById('wizard-top')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	function skipFsc() {
		fsc = null;
		fscSkipped = true;
	}

	async function run() {
		// Catat FSC pra-simulasi hanya bila diisi (bukan 0 / tidak dilewati).
		if (fsc !== null && fsc > 0) {
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
			// Bersihkan sisa agar tidak bocor ke simulasi berikutnya bila gagal.
			sessionStorage.removeItem('fsc_pre');
		}
	}
</script>

<svelte:head><title>Mulai — Financial Twin</title></svelte:head>

<div id="wizard-top" class="mx-auto max-w-3xl scroll-mt-20 px-4 py-6 sm:px-5 sm:py-8">
	<div class="mb-6 flex items-center justify-between gap-3">
		<div>
			<h1 class="text-lg font-bold">Bangun multiverse-mu</h1>
			<p class="text-xs text-[var(--color-ink-dim)]">Selesai dalam &lt; 90 detik · tanpa akun</p>
		</div>
		<div
			class="flex gap-1"
			aria-label={`Progres: langkah ${step + 1} dari ${LAST_STEP + 1}`}
			role="img"
		>
			{#each steps as _s, i}
				<span
					class="h-1.5 w-8 rounded-full transition-colors"
					class:bg-[var(--color-accent)]={i <= step}
					class:bg-[var(--color-line)]={i > step}
				></span>
			{/each}
		</div>
	</div>

	{#if step === 0 && fsc === null && !fscSkipped}
		<div class="card mb-4 p-5">
			<div class="flex items-center justify-between">
				<h2 class="text-base font-bold">
					🧬 Sebelum mulai — seberapa dekat kamu dengan masa depan?
				</h2>
				<button
					type="button"
					class="text-xs text-[var(--color-ink-dim)] hover:underline"
					onclick={skipFsc}
				>
					Lewati
				</button>
			</div>
			<p class="mt-1 text-xs text-[var(--color-ink-dim)]">
				Riset Hershfield (2011) membuktikan: keterhubungan visual dengan diri masa depan
				melipatgandakan tabungan. Opsional — kamu bisa melewatinya.
			</p>
			<div class="mt-3">
				<FutureSelfScale bind:value={fsc} compact />
			</div>
		</div>
	{/if}

	<div class="card p-5 sm:p-6">
		<div class="mb-5 flex items-center justify-between">
			<div>
				<div class="text-xs text-[var(--color-ink-dim)]">
					Langkah {step + 1} dari {LAST_STEP + 1}
				</div>
				<div class="text-sm font-semibold">{steps[step]}</div>
			</div>
			{#if step > 0}
				<button
					type="button"
					class="text-xs hover:underline {confirmReset
						? 'font-semibold text-[var(--color-danger)]'
						: 'text-[var(--color-ink-dim)]'}"
					onclick={resetAll}
				>
					{confirmReset ? 'Yakin? Semua isian dihapus' : 'Mulai dari awal'}
				</button>
			{/if}
		</div>

		{#if step === 0}
			<StepIncome />
		{:else if step === 1}
			<StepPosition />
		{:else if step === 2}
			<StepDecision preselect={preselected ? preselectTemplate : ''} />
		{:else if step === 3}
			<StepAssumption />
		{:else}
			<StepReview onEdit={gotoStep} />
		{/if}

		{#if currentValidation.issues.length}
			<ul class="mt-4 space-y-1.5">
				{#each currentValidation.issues as issue (issue.field + issue.message)}
					<li
						class="flex items-start gap-2 rounded-lg border border-[var(--color-warn)] bg-amber-500/10 p-2.5 text-xs"
					>
						<span aria-hidden="true">⚠️</span>
						<span class="text-[var(--color-ink-dim)]">{issue.message}</span>
					</li>
				{/each}
			</ul>
		{/if}
	</div>

	{#if buildError}
		<div class="mt-4 rounded-xl border border-[var(--color-danger)] bg-red-500/10 p-3 text-sm">
			{buildError}
		</div>
	{/if}

	<div class="mt-5 flex items-center justify-between gap-2">
		<button type="button" class="btn btn-ghost" onclick={back} disabled={step === 0 || building}>
			← Kembali
		</button>
		<button type="button" class="btn btn-primary" onclick={next} disabled={!canNext || building}>
			{#if building}
				Membangun multiverse…
			{:else if step === LAST_STEP}
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
