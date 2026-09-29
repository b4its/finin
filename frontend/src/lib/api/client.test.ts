import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Klien membaca PUBLIC_API_URL dari $env/dynamic/public (SvelteKit).
vi.mock('$env/dynamic/public', () => ({ env: { PUBLIC_API_URL: 'http://test.local' } }));

import { api, streamNarrative } from './client';

function jsonResponse(body: unknown, status = 200): Response {
	return new Response(JSON.stringify(body), {
		status,
		headers: { 'Content-Type': 'application/json' }
	});
}

describe('api client error handling', () => {
	const originalFetch = globalThis.fetch;

	beforeEach(() => {
		vi.restoreAllMocks();
	});

	afterEach(() => {
		globalThis.fetch = originalFetch;
	});

	it('memberi pesan error yang jelas untuk body non-JSON', async () => {
		// Regresi: res.json() lalu res.text() di catch bisa melempar "body already read".
		globalThis.fetch = vi.fn(async () => new Response('Boom internal', { status: 500 })) as never;

		await expect(api.health()).rejects.toThrow(/API 500/);
		await expect(api.health()).rejects.toThrow(/Boom internal/);
	});

	it('mengurai detail JSON pada respons error', async () => {
		globalThis.fetch = vi.fn(async () =>
			jsonResponse({ code: 'NOPE', message: 'gagal' }, 422)
		) as never;

		await expect(api.health()).rejects.toThrow(/NOPE/);
	});

	it('mengembalikan data saat respons sukses', async () => {
		globalThis.fetch = vi.fn(async () =>
			jsonResponse({
				status: 'ok',
				time: 'now',
				engine_version: '2.0.0',
				assumption_set: 'x',
				llm_enabled: false
			})
		) as never;

		const res = await api.health();
		expect(res.status).toBe('ok');
	});

	it('streamNarrative memanggil onDone tanpa onChunk ketika respons error', async () => {
		globalThis.fetch = vi.fn(async () => new Response('nope', { status: 404 })) as never;
		const onChunk = vi.fn();
		const onDone = vi.fn();

		await streamNarrative('sim-1', onChunk, onDone);

		expect(onDone).toHaveBeenCalledTimes(1);
		expect(onChunk).not.toHaveBeenCalled();
	});
});
