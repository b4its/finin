/** Riwayat simulasi lokal (localStorage) — tanpa akun, sesuai prinsip privasi. */

export interface SimRecord {
	id: string;
	created_at: number;
	twin_count: number;
	best_twin: string;
	preset: string;
	/** Ringkasan singkat untuk ditampilkan di daftar. */
	label: string;
	/** Snapshot opsional: net worth riil twin terbaik di tahun ke-10 (untuk daftar). */
	best_net_worth_y10?: number;
	/** Snapshot opsional: pendapatan bulanan saat simulasi dibuat. */
	income_monthly?: number;
}

const KEY = 'ft_history_v1';
const MAX = 24;

function read(): SimRecord[] {
	if (typeof localStorage === 'undefined') return [];
	try {
		const raw = localStorage.getItem(KEY);
		if (!raw) return [];
		const parsed = JSON.parse(raw);
		if (!Array.isArray(parsed)) return [];
		return parsed.filter((r) => r && typeof r.id === 'string') as SimRecord[];
	} catch {
		return [];
	}
}

class HistoryStore {
	items = $state<SimRecord[]>([]);
	loaded = $state(false);

	load(): void {
		this.items = read();
		this.loaded = true;
	}

	add(rec: Omit<SimRecord, 'created_at'> & { created_at?: number }): void {
		const entry: SimRecord = { created_at: Date.now(), ...rec };
		const next = [entry, ...this.items.filter((r) => r.id !== entry.id)].slice(0, MAX);
		this.items = next;
		this.#persist();
	}

	remove(id: string): void {
		this.items = this.items.filter((r) => r.id !== id);
		this.#persist();
	}

	clear(): void {
		this.items = [];
		this.#persist();
	}

	#persist(): void {
		if (typeof localStorage === 'undefined') return;
		try {
			localStorage.setItem(KEY, JSON.stringify(this.items));
		} catch {
			/* storage penuh / private mode -> abaikan */
		}
	}
}

export const history = new HistoryStore();
