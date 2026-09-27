import { defineConfig } from '@playwright/test';

const PORT = process.env.FRONTEND_PORT ?? '5245';

export default defineConfig({
	testDir: './tests',
	timeout: 60_000,
	expect: { timeout: 10_000 },
	fullyParallel: false,
	retries: 1,
	reporter: [['list']],
	use: {
		baseURL: `http://localhost:${PORT}`,
		headless: true,
		trace: 'on-first-retry'
	}
});
