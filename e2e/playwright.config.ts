import { basename } from "node:path";
import { defineConfig, devices } from "@playwright/test";

const dir = basename(process.cwd()) === "e2e" ? process.cwd() : "e2e";
const port = process.env.E2E_PORT ?? "5173";
const baseUrl = `http://localhost:${port}`;
const defaultGraphqlPort = process.env.E2E_GRAPHQL_PORT ?? "8000";
const graphqlUrl =
	process.env.E2E_GRAPHQL_URL ??
	`http://localhost:${defaultGraphqlPort}/graphql`;
const parsedGraphqlUrl = new URL(graphqlUrl);
const graphqlPort =
	parsedGraphqlUrl.port ||
	(parsedGraphqlUrl.protocol === "https:" ? "443" : "80");

export default defineConfig({
	testDir: "./src/tests",
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 2 : 0,
	workers: process.env.CI ? 1 : undefined,
	reporter: "html",
	use: {
		baseURL: baseUrl,
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
			command: `bun run dev -- --port ${port}`,
			cwd: dir,
			url: baseUrl,
			reuseExistingServer: !process.env.CI,
		},
		{
			// FastAPI server with GraphiQL
			// In CI, this is started by the workflow; locally we start it here
			command: `uv run --no-sync fastapi dev app.py --port ${graphqlPort}`,
			url: graphqlUrl,
			reuseExistingServer: true,
			cwd: dir,
		},
	],
});
