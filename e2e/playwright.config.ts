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
			// Strawberry server with GraphiQL
			// In CI, this is started by the workflow; locally we start it here
			command: "poetry run strawberry dev app:schema --port 8000",
			url: "http://localhost:8000",
			reuseExistingServer: true,
			cwd: "..",
		},
	],
});
