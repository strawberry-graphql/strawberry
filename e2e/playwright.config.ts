import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
	testDir: "./src/tests",
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 2 : 0,
	workers: process.env.CI ? 1 : undefined,
	reporter: "html",
	use: {
		baseURL: "http://localhost:5173",
		trace: "on-first-retry",
	},
	projects: [
		{
			name: "chromium",
			use: { ...devices["Desktop Chrome"] },
		},
	],
	webServer: [
		{
			command: "bun run dev",
			url: "http://localhost:5173",
			reuseExistingServer: !process.env.CI,
		},
		{
			command: "../.venv/bin/python graphiql_server.py",
			url: "http://localhost:8000",
			reuseExistingServer: !process.env.CI,
		},
	],
});
