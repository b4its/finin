/** Store notifikasi toast global (Svelte 5 runes). */

export type ToastKind = 'success' | 'error' | 'info' | 'warn';

export interface Toast {
	id: number;
	kind: ToastKind;
	message: string;
	/** ms sebelum auto-dismiss; 0 = tidak auto-dismiss. */
	duration: number;
}

let nextId = 1;

class ToastStore {
	items = $state<Toast[]>([]);

	show(kind: ToastKind, message: string, duration = 4000): number {
		const id = nextId++;
		this.items = [...this.items, { id, kind, message, duration }];
		if (duration > 0) {
			setTimeout(() => this.dismiss(id), duration);
		}
		return id;
	}

	success(message: string, duration?: number): number {
		return this.show('success', message, duration);
	}

	error(message: string, duration?: number): number {
		return this.show('error', message, duration ?? 6000);
	}

	info(message: string, duration?: number): number {
		return this.show('info', message, duration);
	}

	warn(message: string, duration?: number): number {
		return this.show('warn', message, duration);
	}

	dismiss(id: number): void {
		this.items = this.items.filter((t) => t.id !== id);
	}

	clear(): void {
		this.items = [];
	}
}

export const toast = new ToastStore();
