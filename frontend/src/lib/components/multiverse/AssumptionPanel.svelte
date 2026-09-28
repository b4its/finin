<script lang="ts">
	import { api } from '$lib/api/client';
	import type { AssumptionsSnapshot } from '$lib/api/types';
	import { percent, dateID, isStale } from '$lib/utils/format';

	let {
		assumptions,
		overrides = $bindable({} as Record<string, unknown>),
		onRecompute
	}: {
		assumptions: AssumptionsSnapshot;
		overrides?: Record<string, unknown>;
		onRecompute?: (overrides: Record<string, unknown>) => void;
	} = $props();

	let open = $state(false);
	let edit = $state(false);
	let fresh = $state<AssumptionsSnapshot | null>(null);
	let dirty = $state(false);

	let current = $derived(fresh ?? assumptions);
	let stale = $derived(isStale(current.as_of));

	async function toggle() {
		open = !open;
		if (open && !fresh) {
			try {
				fresh = await api.assumptions(current.preset);
			} catch {
				/* biarkan pakai yang ada */
			}
		}
	}

	const presets = [
		{ key: 'konservatif', label: 'Konservatif' },
		{ key: 'moderat', label: 'Moderat' },
		{ key: 'optimis', label: 'Optimis' }
	];

	// Parameter yang boleh diedit manual.
	const editable = [
		{ key: 'inflation', label: 'Inflasi', group: '', hint: '2–6%/th' },
		{ key: 'salary_growth', label: 'Kenaikan gaji', group: '', hint: '1–12%/th' },
		{ key: 's2_salary_premium', label: 'Premi gaji S2', group: '', hint: '5–35%' },
		{ key: 'savings', label: 'Tabungan bank', returns: true, hint: '0–6%/th' },
		{ key: 'deposit', label: 'Deposito', returns: true, hint: '0–6%/th' },
		{ key: 'money_market', label: 'Reksa dana pasar uang', returns: true, hint: '1–8%/th' },
		{ key: 'bond', label: 'SBN ritel', returns: true, hint: '3–10%/th' },
		{ key: 'stock', label: 'Reksa dana indeks saham', returns: true, hint: '0–15%/th' }
	];

	function overrideValue(key: string, returns: boolean | undefined, fallback: number): number {
		if (returns) {
			const r = overrides.returns as Record<string, number> | undefined;
			return r?.[key] ?? fallback;
		}
		const v = overrides[key];
		return typeof v === 'number' ? v : fallback;
	}

	function setOverride(key: string, returns: boolean | undefined, value: number) {
		if (returns) {
			const r = { ...((overrides.returns as Record<string, number>) ?? {}) };
			r[key] = value;
			overrides = { ...overrides, returns: r };
		} else {
			overrides = { ...overrides, [key]: value };
		}
		dirty = true;
	}

	function resetOverrides() {
		overrides = {};
		dirty = false;
	}

	function apply() {
		onRecompute?.(overrides);
		dirty = false;
	}
</script>

<div class="card overflow-hidden">
	<button class="flex w-full items-center justify-between p-4 text-left" onclick={toggle}>
		<div>
			<div class="text-sm font-semibold">Asumsi & sumber</div>
			<div class="text-xs text-[var(--color-ink-dim)]">
				Set {current.code} · data per {dateID(current.as_of)}
			</div>
		</div>
		<span class="text-[var(--color-ink-dim)]">{open ? '▲' : '▼'}</span>
	</button>

	{#if open}
		<div class="border-t border-[var(--color-line)] p-4">
			{#if stale}
				<div class="mb-3 rounded-xl border border-[var(--color-warn)] bg-amber-500/10 p-3 text-xs">
					⚠️ Data ini berumur lebih dari 6 bulan. Periksa kesegaran sumber sebelum mengambil
					keputusan.
				</div>
			{/if}

			<h4 class="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
				Parameter terpakai
			</h4>
			<div class="grid grid-cols-1 gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
				{#each Object.entries(current.values) as [k, v]}
					{#if typeof v === 'number'}
						<div class="flex justify-between border-b border-[var(--color-line)] py-1.5">
							<span class="capitalize text-[var(--color-ink-dim)]">{k.replace('_', ' ')}</span>
							<span class="num font-medium">{percent(v)}</span>
						</div>
					{:else if k === 'returns' && typeof v === 'object'}
						{#each Object.entries(v as Record<string, number>) as [rk, rv]}
							<div class="flex justify-between border-b border-[var(--color-line)] py-1.5">
								<span class="text-[var(--color-ink-dim)]">imbal {rk.replace('_', ' ')}</span>
								<span class="num font-medium">{percent(rv)}</span>
							</div>
						{/each}
					{/if}
				{/each}
			</div>

			{#if onRecompute}
				<div class="mt-4 flex items-center justify-between">
					<h4 class="text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]">
						Edit manual
					</h4>
					<button class="chip" class:active={edit} onclick={() => (edit = !edit)}>
						{edit ? 'Tutup editor' : 'Ubah asumsi'}
					</button>
				</div>
				{#if edit}
					<div class="mt-2 space-y-3 rounded-xl border border-[var(--color-line)] p-3">
						<p class="text-xs text-[var(--color-ink-dim)]">
							Geser nilai lalu tekan “Hitung ulang” untuk melihat dampaknya. Ini untuk eksplorasi —
							nilai default tetap jadi acuan.
						</p>
						{#each editable as e}
							{@const base = e.returns
								? (current.values.returns?.[e.key] ?? 0)
								: ((current.values[e.key] as number) ?? 0)}
							{@const val = overrideValue(e.key, e.returns, base)}
							{@const overridden = Math.abs(val - base) > 1e-9}
							<label class="block">
								<div class="flex items-center justify-between text-xs">
									<span class={overridden ? 'font-semibold text-[var(--color-accent)]' : ''}
										>{e.label}{#if e.returns}
											(imbal){/if}</span
									>
									<span class="num">{percent(val)}</span>
								</div>
								<input
									type="range"
									min="0"
									max="0.2"
									step="0.001"
									value={val}
									oninput={(ev) =>
										setOverride(
											e.key,
											e.returns,
											parseFloat((ev.target as HTMLInputElement).value)
										)}
									class="mt-1 w-full accent-[var(--color-accent)]"
									aria-label={`${e.label} ${percent(val)}`}
								/>
								<span class="text-[0.65rem] text-[var(--color-ink-dim)]">{e.hint}</span>
							</label>
						{/each}
						<div class="flex flex-wrap gap-2 pt-1">
							<button class="btn btn-primary !py-1.5 !text-xs" onclick={apply} disabled={!dirty}>
								Hitung ulang dengan asumsi ini
							</button>
							<button class="btn btn-ghost !py-1.5 !text-xs" onclick={resetOverrides}>
								Reset ke default
							</button>
						</div>
					</div>
				{/if}
			{/if}

			<h4
				class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]"
			>
				Regulasi OJK ({current.regulatory.version})
			</h4>
			<div
				class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-3 text-xs"
			>
				<p>
					Mencabut: {current.regulatory.replaces} · berlaku {dateID(
						current.regulatory.effective_from
					)}
				</p>
				<ul class="mt-2 space-y-1">
					{#each current.regulatory.consumer_caps as c}
						<li>
							Bunga maks {percent(c.rate_daily_max, 2)}/hari untuk tenor
							{c.tenor_max_months
								? `≤ ${c.tenor_max_months} bulan`
								: `> ${current.regulatory.consumer_caps[0].tenor_max_months} bulan`}
							(denda sama).
						</li>
					{/each}
					<li>Lock cap: bunga + denda ≤ {percent(current.regulatory.lock_cap_ratio, 0)} pokok.</li>
					<li>
						Batas rasio cicilan: {percent(current.regulatory.dsr_cap, 0)} penghasilan (sejak 2026).
					</li>
					<li>Macet (TWP90): tunggakan &gt; {current.regulatory.default_days} hari.</li>
				</ul>
			</div>

			<h4
				class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]"
			>
				Sumber
			</h4>
			<ul class="space-y-1.5 text-xs">
				{#each Object.entries(current.sources) as [k, s]}
					<li class="flex flex-wrap items-baseline gap-1.5">
						<span class="font-medium text-[var(--color-ink)]">{k}:</span>
						{#if s.url}
							<a
								href={s.url}
								target="_blank"
								rel="noreferrer"
								class="text-[var(--color-accent)] underline">{s.label}</a
							>
						{:else}
							<span class="text-[var(--color-ink-dim)]">{s.label}</span>
						{/if}
						<span class="chip !py-0 !text-[0.6rem] text-[var(--color-ink-dim)]"
							>{dateID(s.as_of)}</span
						>
						{#if s.kind === 'assumption'}
							<span class="chip !py-0 !text-[0.6rem] border-amber-500/40 text-[var(--color-warn)]"
								>asumsi</span
							>
						{/if}
					</li>
				{/each}
			</ul>

			{#if current.market_context?.length}
				<h4
					class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]"
				>
					Konteks pasar (data masalah)
				</h4>
				<ul class="space-y-1 text-xs text-[var(--color-ink-dim)]">
					{#each current.market_context as m}
						<li>• {m.label} <span class="opacity-70">— {m.source}</span></li>
					{/each}
				</ul>
			{/if}

			<h4
				class="mb-2 mt-4 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-dim)]"
			>
				Preset sensitivitas
			</h4>
			<div class="overflow-x-auto">
				<table class="w-full text-xs">
					<thead class="text-[var(--color-ink-dim)]">
						<tr>
							<th scope="col" class="px-2 py-1 text-left font-medium">Parameter</th>
							{#each presets as p}<th scope="col" class="px-2 py-1 text-right font-medium"
									>{p.label}</th
								>{/each}
						</tr>
					</thead>
					<tbody class="num">
						<tr>
							<td class="px-2 py-1 family-sans">Inflasi</td>
							{#each presets as p}<td class="px-2 py-1 text-right"
									>{percent((current.presets[p.key]?.inflation as number) ?? 0)}</td
								>{/each}
						</tr>
						<tr>
							<td class="px-2 py-1">Kenaikan gaji</td>
							{#each presets as p}<td class="px-2 py-1 text-right"
									>{percent((current.presets[p.key]?.salary_growth as number) ?? 0)}</td
								>{/each}
						</tr>
						<tr>
							<td class="px-2 py-1">Premi S2</td>
							{#each presets as p}<td class="px-2 py-1 text-right"
									>{percent((current.presets[p.key]?.s2_salary_premium as number) ?? 0)}</td
								>{/each}
						</tr>
						<tr>
							<td class="px-2 py-1">Pasar uang</td>
							{#each presets as p}<td class="px-2 py-1 text-right"
									>{percent(
										(current.presets[p.key]?.returns as Record<string, number>)?.money_market ?? 0
									)}</td
								>{/each}
						</tr>
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>
