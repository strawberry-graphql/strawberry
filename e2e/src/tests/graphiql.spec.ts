import { expect, type Page, test } from "@playwright/test";

test.describe("GraphiQL URL Sharing Tests", () => {
	const GRAPHIQL_URL = "http://localhost:8000";

	// Helper to wait for GraphiQL to fully load
	async function waitForGraphiQL(page: Page) {
		// Wait for the execute button which only appears after React renders
		await page.waitForSelector(".graphiql-execute-button", { timeout: 30000 });
	}

	test("loads default example query when no URL params", async ({
		page,
	}: { page: Page }) => {
		await page.goto(GRAPHIQL_URL);
		await waitForGraphiQL(page);

		// Check that the default example query is shown
		const queryEditor = page.locator(".graphiql-query-editor");
		await expect(queryEditor).toContainText("Welcome to GraphiQL");
	});

	test("loads query from URL parameter", async ({ page }: { page: Page }) => {
		const testQuery = "{ hello }";
		const encodedQuery = encodeURIComponent(testQuery);

		await page.goto(`${GRAPHIQL_URL}?query=${encodedQuery}`);
		await waitForGraphiQL(page);

		// Check that the query from URL is loaded
		const queryEditor = page.locator(".graphiql-query-editor");
		await expect(queryEditor).toContainText("hello");
	});

	test("loads variables from URL parameter", async ({
		page,
	}: { page: Page }) => {
		const testQuery = "query Hello($name: String!) { hello(name: $name) }";
		const testVariables = '{"name": "Test"}';

		await page.goto(
			`${GRAPHIQL_URL}?query=${encodeURIComponent(testQuery)}&variables=${encodeURIComponent(testVariables)}`,
		);
		await waitForGraphiQL(page);

		// Open variables editor
		const variablesTab = page.locator('button:has-text("Variables")');
		await variablesTab.click();

		// Check that variables are loaded
		const variablesEditor = page.locator(".graphiql-editor-tool");
		await expect(variablesEditor).toContainText("name");
		await expect(variablesEditor).toContainText("Test");
	});

	test("updates URL when query is edited", async ({ page }: { page: Page }) => {
		await page.goto(GRAPHIQL_URL);
		await waitForGraphiQL(page);

		// Focus the query editor and clear it
		const queryEditor = page.locator(".graphiql-query-editor .cm-content");
		await queryEditor.click();

		// Select all and type new query
		await page.keyboard.press("Meta+a");
		await page.keyboard.type("{ hello }");

		// Wait for URL to update
		await page.waitForFunction(() => {
			return window.location.search.includes("query=");
		});

		// Check that URL contains the query
		const url = page.url();
		expect(url).toContain("query=");
		expect(url).toContain(encodeURIComponent("{ hello }"));
	});

	test("persists query after page reload", async ({ page }: { page: Page }) => {
		const testQuery = "{ add(a: 1, b: 2) }";

		await page.goto(`${GRAPHIQL_URL}?query=${encodeURIComponent(testQuery)}`);
		await waitForGraphiQL(page);

		// Verify query is loaded
		const queryEditor = page.locator(".graphiql-query-editor");
		await expect(queryEditor).toContainText("add");

		// Reload the page
		await page.reload();
		await waitForGraphiQL(page);

		// Verify query is still there
		await expect(queryEditor).toContainText("add");
	});

	test("can execute query loaded from URL", async ({
		page,
	}: { page: Page }) => {
		const testQuery = "{ hello }";

		await page.goto(`${GRAPHIQL_URL}?query=${encodeURIComponent(testQuery)}`);
		await waitForGraphiQL(page);

		// Click the execute button
		const executeButton = page.locator(".graphiql-execute-button");
		await executeButton.click();

		// Wait for response
		const responseEditor = page.locator(".graphiql-response");
		await expect(responseEditor).toContainText("Hello, World!", {
			timeout: 10000,
		});
	});

	test("loads headers from URL parameter", async ({
		page,
	}: { page: Page }) => {
		const testQuery = "{ hello }";
		const testHeaders = '{"Authorization": "Bearer token123"}';

		await page.goto(
			`${GRAPHIQL_URL}?query=${encodeURIComponent(testQuery)}&headers=${encodeURIComponent(testHeaders)}`,
		);
		await waitForGraphiQL(page);

		// Open headers editor
		const headersTab = page.locator('button:has-text("Headers")');
		await headersTab.click();

		// Check that headers are loaded
		const headersEditor = page.locator(".graphiql-editor-tool");
		await expect(headersEditor).toContainText("Authorization");
		await expect(headersEditor).toContainText("Bearer token123");
	});
});
