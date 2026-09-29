<script lang="ts">
	import Badge from '$lib/components/ui/Badge.svelte';
	import Disclaimer from '$lib/components/ui/Disclaimer.svelte';
	import FutureSelfScale from '$lib/components/ui/FutureSelfScale.svelte';
	import { sim } from '$lib/stores/simulation.svelte';
	import type { Recommendation, Twin } from '$lib/api/types';
	import { api } from '$lib/api/client';

	let {
		recommendation,
		twins,
		simulationId
	}: { recommendation: Recommendation | null; twins: Twin[]; simulationId: string } = $props();

	let committed = $state(false);
	let showPost = $state(false);
	let fscPost = $state<number | null>(null);
	let submittedPost = $state(false);
	let copied = $state(false);

	let fscPre = $derived(sim.fscPre);
	let best = $derived(twins.find((t) => t.code === recommendation?.best_twin));

	async function commit() {
		try {
			await api.recordEvent(simulationId, 'commit');
			committed = true;
			showPost = true;
		} catch {
			committed = true;
		}
	}

	async function submitPost(v: number) {
		fscPost = v;
		try {
			// fsc_pre sudah dicatat sekali saat simulasi dibuat (routes/start).
			// Di sini cukup catat fsc_post agar fsc_pre tidak terhitung ganda
			// setiap kali skala pasca diubah.
			await api.recordEvent(simulationId, 'fsc_post', v);
			submittedPost = true;
		} catch {
			submittedPost = true;
		}
	}

	async function copyLink() {
		try {
			await navigator.clipboard.writeText(window.location.href);
			copied = true;
			setTimeout(() => (copied = false), 1800);
		} catch {
			/* diabaikan */
		}
	}
</script>

<div class="card p-5" style="border-color: {best?.color ?? 'var(--color-line)'}">
	<div class="flex flex-wrap items-center justify-between gap-2">
		<div class="flex items-center gap-2">
			<span class="text-lg">🎯</span>
			<h3 class="text-base font-bold">Rekomendasi</h3>
		</div>
		{#if recommendation}<Badge level="info"
				>{recommendation.source === 'llm' ? 'Narasi AI' : 'Fallback template'}</Badge
			>{/if}
	</div>

	{#if recommendation && best}
		<div class="mt-3 flex items-center gap-2">
			<span class="inline-block h-3 w-3 rounded-full" style="background:{best.color}"></span>
			<span class="font-semibold">{recommendation.best_label}</span>
			<span class="text-xs text-[var(--color-ink-dim)]"
				>(skor {(best.score * 100).toFixed(0)}/100)</span
			>
		</div>

		<div class="mt-4 rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4">
			<div class="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
				Langkah pertama hari ini
			</div>
			<p class="text-sm leading-relaxed">{recommendation.first_step}</p>
		</div>

		<div class="mt-3 text-sm leading-relaxed text-[var(--color-ink-dim)]">
			{recommendation.rationale}
		</div>

		<div class="mt-4 flex flex-wrap gap-2">
			<button class="btn btn-primary" onclick={commit} disabled={committed}>
				{committed ? '✓ Terkomit' : 'Saya komit langkah ini'}
			</button>
			<button class="btn btn-ghost" onclick={copyLink}
				>{copied ? '✓ Tersalin' : 'Salin link hasil'}</button
			>
		</div>

		{#if showPost}
			<div class="mt-4 rounded-xl border border-[var(--color-accent)] bg-blue-500/5 p-4 space-y-3">
				<div>
					<p class="text-sm font-semibold">
						🧬 Evaluasi Pasca-Simulasi: Seberapa dekat kamu dengan dirimu di masa depan sekarang?
					</p>
					<p class="mt-0.5 text-xs text-[var(--color-ink-dim)]">
						Setelah melihat proyeksi 5, 10, dan 20 tahun di multiverse (1–7):
					</p>
				</div>
				<FutureSelfScale bind:value={fscPost} onchange={submitPost} compact />
				{#if submittedPost}
					<div
						class="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-2.5 text-xs text-emerald-400"
					>
						✓ Evaluasi tersimpan!
						{#if fscPre !== null && fscPre > 0 && fscPost !== null}
							{@const delta = fscPost - fscPre}
							<span class="font-semibold ml-1">
								Skor kedekatan: {fscPre} → {fscPost} ({delta >= 0 ? `+${delta}` : delta} poin).
								{delta > 0
									? 'Keterhubungan masa depanmu meningkat!'
									: 'Persepsi masa depanmu telah dipetakan.'}
							</span>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	{:else}
		<p class="mt-3 text-sm text-[var(--color-ink-dim)]">Menghitung rekomendasi…</p>
	{/if}

	<div class="mt-4">
		<Disclaimer variant="compact" />
	</div>
</div>
