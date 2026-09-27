<script lang="ts">
	import type { Twin } from '$lib/api/types';
	import Modal from '$lib/components/ui/Modal.svelte';
	import { rupiahBrief, percent, rupiah } from '$lib/utils/format';
	import { twinIcon } from '$lib/utils/icons';
	import { onMount } from 'svelte';

	let {
		open = $bindable(false),
		twins,
		bestCode,
		simId,
		preset = 'moderat'
	}: {
		open: boolean;
		twins: Twin[];
		bestCode: string | null;
		simId: string;
		preset?: string;
	} = $props();

	let canvasEl = $state<HTMLCanvasElement | null>(null);
	let copiedText = $state(false);
	let copiedImage = $state(false);

	let bestTwin = $derived(twins.find((t) => t.code === bestCode) ?? twins[1] ?? twins[0]);
	let baseline = $derived(twins.find((t) => t.code === '0') ?? twins[0]);

	let bestPt10 = $derived(bestTwin?.yearly_series.find((p) => p.year === 10) ?? bestTwin?.yearly_series[bestTwin.yearly_series.length - 1]);
	let basePt10 = $derived(baseline?.yearly_series.find((p) => p.year === 10) ?? baseline?.yearly_series[baseline.yearly_series.length - 1]);

	let nw10 = $derived(bestPt10?.net_worth ?? 0);
	let nwReal10 = $derived(bestPt10?.net_worth_real ?? 0);
	let baseNw10 = $derived(basePt10?.net_worth ?? 0);
	let delta = $derived(nw10 - baseNw10);
	let pctAdvantage = $derived(baseNw10 > 0 ? (nw10 - baseNw10) / baseNw10 : 0);

	let shareUrl = $derived(typeof window !== 'undefined' ? window.location.href : `https://finin.id/sim/${simId}`);

	let shareText = $derived(
		`🌌 Hasil Simulasi Multiverse Finansialku di Finin!\n\n` +
		`🏆 Persona Terpilih: Twin ${bestTwin?.code} (${bestTwin?.label})\n` +
		`📈 Proyeksi Net Worth Th-10: ${rupiahBrief(nw10)} (Nilai Riil: ${rupiahBrief(nwReal10)})\n` +
		`🚀 Keuntungan vs Baseline: ${delta >= 0 ? '+' : ''}${rupiahBrief(delta)} (${percent(pctAdvantage, 0)})\n` +
		`🛡️ Dana Darurat Aman: ${(bestPt10?.emergency_months ?? 0).toFixed(1)} bulan · DSR: ${percent(bestPt10?.dsr ?? 0, 0)}\n\n` +
		`Cek simulasi lengkap dan uji keputusan finansialmu di:\n${shareUrl}`
	);

	function drawCard() {
		if (!canvasEl || !bestTwin) return;
		const ctx = canvasEl.getContext('2d');
		if (!ctx) return;

		const w = 1200;
		const h = 630;
		canvasEl.width = w;
		canvasEl.height = h;

		// Background gradient
		const grad = ctx.createLinearGradient(0, 0, w, h);
		grad.addColorStop(0, '#0a0e17');
		grad.addColorStop(0.5, '#0f172a');
		grad.addColorStop(1, '#050811');
		ctx.fillStyle = grad;
		ctx.fillRect(0, 0, w, h);

		// Glow accent circles
		const g1 = ctx.createRadialGradient(200, 150, 10, 200, 150, 350);
		g1.addColorStop(0, 'rgba(56, 189, 248, 0.15)');
		g1.addColorStop(1, 'transparent');
		ctx.fillStyle = g1;
		ctx.fillRect(0, 0, w, h);

		const g2 = ctx.createRadialGradient(1000, 500, 10, 1000, 500, 400);
		g2.addColorStop(0, 'rgba(129, 140, 248, 0.15)');
		g2.addColorStop(1, 'transparent');
		ctx.fillStyle = g2;
		ctx.fillRect(0, 0, w, h);

		// Border glow frame
		ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
		ctx.lineWidth = 2;
		ctx.strokeRect(30, 30, w - 60, h - 60);

		// Header logo & title
		ctx.font = 'bold 24px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#38bdf8';
		ctx.fillText('FININ · FINANCIAL MULTIVERSE SIMULATOR', 60, 80);

		ctx.font = '16px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#94a3b8';
		ctx.fillText('Proyeksi Ceteris Paribus 240 Bulan · OJK SEOJK 19/2025 Compliant', 60, 110);

		// Badge Persona Winner
		ctx.fillStyle = 'rgba(56, 189, 248, 0.12)';
		ctx.beginPath();
		ctx.roundRect(60, 145, 520, 44, 8);
		ctx.fill();
		ctx.strokeStyle = '#38bdf8';
		ctx.lineWidth = 1;
		ctx.stroke();

		ctx.font = 'bold 16px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#38bdf8';
		ctx.fillText('🏆  KEPUTUSAN FINANSIAL MULTIVERSE TERUNGGUL', 80, 173);

		// Persona Label
		ctx.font = '900 46px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#f8fafc';
		ctx.fillText(`${bestTwin.label}`, 60, 245);

		ctx.font = '20px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#cbd5e1';
		ctx.fillText(`Twin ${bestTwin.code} · ${bestTwin.description.slice(0, 80)}...`, 60, 285);

		// Stat box 1: Net Worth Th-10
		ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
		ctx.beginPath();
		ctx.roundRect(60, 325, 330, 150, 16);
		ctx.fill();
		ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
		ctx.stroke();

		ctx.font = '15px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#94a3b8';
		ctx.fillText('NET WORTH TAHUN KE-10', 85, 360);

		ctx.font = 'bold 36px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#38bdf8';
		ctx.fillText(rupiahBrief(nw10), 85, 410);

		ctx.font = '15px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#64748b';
		ctx.fillText(`Nilai Riil Hari Ini: ${rupiahBrief(nwReal10)}`, 85, 445);

		// Stat box 2: Keuntungan vs Baseline
		ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
		ctx.beginPath();
		ctx.roundRect(420, 325, 330, 150, 16);
		ctx.fill();
		ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
		ctx.stroke();

		ctx.font = '15px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#94a3b8';
		ctx.fillText('KEUNGGULAN VS BASELINE', 445, 360);

		ctx.font = 'bold 36px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = delta >= 0 ? '#34d399' : '#f87171';
		ctx.fillText(`${delta >= 0 ? '+' : ''}${rupiahBrief(delta)}`, 445, 410);

		ctx.font = '15px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = delta >= 0 ? '#34d399' : '#f87171';
		ctx.fillText(`${percent(pctAdvantage, 0)} lebih unggul dari Tanpa Perubahan`, 445, 445);

		// Stat box 3: Ketahanan & OJK
		ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
		ctx.beginPath();
		ctx.roundRect(780, 325, 360, 150, 16);
		ctx.fill();
		ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
		ctx.stroke();

		ctx.font = '15px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#94a3b8';
		ctx.fillText('STABILITAS & DSR OJK', 805, 360);

		ctx.font = 'bold 32px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#a78bfa';
		ctx.fillText(`Dana Darurat ${(bestPt10?.emergency_months ?? 0).toFixed(1)} bln`, 805, 410);

		ctx.font = '15px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = (bestPt10?.dsr ?? 0) <= 0.3 ? '#34d399' : '#fb923c';
		ctx.fillText(`DSR ${percent(bestPt10?.dsr ?? 0, 0)} (Batas OJK ≤ 30%)`, 805, 445);

		// Footer
		ctx.font = '15px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#64748b';
		ctx.fillText(`Preset: ${preset.toUpperCase()} · Simulasi ID: ${simId.slice(0, 8)} · https://finin.id`, 60, 560);

		ctx.font = 'bold 15px system-ui, -apple-system, sans-serif';
		ctx.fillStyle = '#38bdf8';
		ctx.fillText('Temukan Kembaran Finansial Masa Depanmu', 800, 560);
	}

	$effect(() => {
		if (open) {
			// tunggu DOM selesai render
			setTimeout(() => drawCard(), 60);
		}
	});

	function downloadPng() {
		if (!canvasEl) return;
		const a = document.createElement('a');
		a.download = `finin-multiverse-twin-${bestTwin.code}.png`;
		a.href = canvasEl.toDataURL('image/png');
		a.click();
	}

	async function copyImageToClipboard() {
		if (!canvasEl || !navigator.clipboard) return;
		try {
			canvasEl.toBlob(async (blob) => {
				if (!blob) return;
				await navigator.clipboard.write([
					new ClipboardItem({ 'image/png': blob })
				]);
				copiedImage = true;
				setTimeout(() => (copiedImage = false), 2500);
			});
		} catch {
			// fallback
			downloadPng();
		}
	}

	async function copyTextToClipboard() {
		if (!navigator.clipboard) return;
		await navigator.clipboard.writeText(shareText);
		copiedText = true;
		setTimeout(() => (copiedText = false), 2500);
	}

	function shareToWhatsApp() {
		const encoded = encodeURIComponent(shareText);
		window.open(`https://api.whatsapp.com/send?text=${encoded}`, '_blank');
	}

	function shareToTwitter() {
		const tweet = encodeURIComponent(
			`🌌 Multiverse finansialku membuktikan keputusanku di Finin!\n\n` +
			`Twin ${bestTwin.code} (${bestTwin.label}) unggul ${rupiahBrief(delta)} di tahun ke-10.\n` +
			`Coba uji keputusan finansialmu: ${shareUrl}\n\n#Finin #CerdasFinansial #OJK`
		);
		window.open(`https://twitter.com/intent/tweet?text=${tweet}`, '_blank');
	}
</script>

<Modal bind:open title="✨ Bagikan Hasil Multiverse Finansial">
	<div class="space-y-5">
		<p class="text-sm text-[var(--color-ink-dim)]">
			Bagikan temuan simulasi multiverse-mu ke WhatsApp, media sosial, atau simpan kartu persona digital sebagai pengingat tujuan finansialmu.
		</p>

		<!-- Canvas Preview Container -->
		<div class="relative overflow-hidden rounded-xl border border-[var(--color-line)] bg-slate-950 p-2 shadow-2xl">
			<canvas
				bind:this={canvasEl}
				class="w-full rounded-lg shadow-inner"
				style="aspect-ratio: 1200 / 630;"
			></canvas>
		</div>

		<!-- Tombol Aksi Gambar -->
		<div class="flex flex-wrap gap-2.5">
			<button class="btn btn-primary flex-1 !text-xs font-semibold" onclick={downloadPng}>
				📥 Unduh Kartu Persona (.PNG)
			</button>
			<button class="btn btn-ghost flex-1 !text-xs font-semibold" onclick={copyImageToClipboard}>
				{copiedImage ? '✓ Gambar Tersalin!' : '📋 Salin Gambar ke Clipboard'}
			</button>
		</div>

		<!-- Media Sosial & Pesan Cepat -->
		<div class="rounded-xl border border-[var(--color-line)] bg-[var(--color-void-2)] p-4 space-y-3">
			<span class="text-xs font-semibold text-[var(--color-ink-dim)] block">Kirim Langsung:</span>
			<div class="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
				<button
					class="btn !bg-emerald-600 hover:!bg-emerald-500 text-white !text-xs font-semibold py-2.5"
					onclick={shareToWhatsApp}
				>
					💬 Kirim ke WhatsApp
				</button>
				<button
					class="btn !bg-sky-500 hover:!bg-sky-400 text-white !text-xs font-semibold py-2.5"
					onclick={shareToTwitter}
				>
					🐦 Share di X / Twitter
				</button>
				<button
					class="btn btn-ghost !text-xs font-semibold py-2.5"
					onclick={copyTextToClipboard}
				>
					{copiedText ? '✓ Teks Tersalin!' : '📄 Salin Teks Ringkasan'}
				</button>
			</div>
		</div>
	</div>
</Modal>
