/**
 * Store status backend (Svelte 5 runes).
 *
 * Melakukan probe ke /health secara berkala dan menyimpan status agar UI bisa
 * menampilkan indikator "terhubung / terputus / memeriksa". Membantu pengguna
 * memahami ketika backend sedang tidak dapat dijangkau sebelum mereka mulai
 * simulasi (bukan setelah gagal).
 */

import { api, type HealthStatus } from '$lib/api/client';

export type ConnState = 'unknown' | 'checking' | 'online' | 'offline';

class HealthStore {
	state = $state<ConnState>('unknown');
	info = $state<HealthStatus | null>(null);
	lastChecked = $state<number | null>(null);

	#timer: ReturnType<typeof setInterval> | null = null;
	#controller: AbortController | null = null;
	#generation = 0;

	async check(timeoutMs = 6_000) {
		const generation = ++this.#generation;
		this.#controller?.abort();
		const ctrl = new AbortController();
		this.#controller = ctrl;
		this.state = this.state === 'unknown' ? 'checking' : this.state;
		const timeout = setTimeout(() => ctrl.abort(), timeoutMs);
		try {
			const info = await api.health({ signal: ctrl.signal });
			if (generation !== this.#generation) return;
			this.info = info;
			this.state = 'online';
		} catch {
			if (generation !== this.#generation) return;
			this.info = null;
			this.state = 'offline';
		} finally {
			clearTimeout(timeout);
			if (generation === this.#generation) {
				this.#controller = null;
				this.lastChecked = Date.now();
			}
		}
	}

	/** Mulai polling berkala (idempoten — tidak menumpuk interval). */
	start(intervalMs = 30_000) {
		if (this.#timer) return;
		this.check();
		this.#timer = setInterval(() => this.check(), intervalMs);
	}

	stop() {
		this.#generation++;
		this.#controller?.abort();
		this.#controller = null;
		if (this.#timer) {
			clearInterval(this.#timer);
			this.#timer = null;
		}
	}
}

export const health = new HealthStore();
