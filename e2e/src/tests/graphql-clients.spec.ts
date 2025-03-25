import { test, expect, type Page } from "@playwright/test";

test.describe("GraphQL Client Tests", () => {
	test.beforeEach(async ({ page }: { page: Page }) => {
		// Navigate to the test page
		await page.goto("/");
	});

	test.describe("Apollo Tests", () => {
		test("basic query works", async ({ page }: { page: Page }) => {
			const button = page.getByTestId("apollo-basic-query-button");
			await button.scrollIntoViewIfNeeded();
			await button.click();

			// Verify the exact result
			const result = page.getByTestId("apollo-basic-query-result");
			await expect(result).toContainText('"hello": "Hello, world!"');
		});

		test("delayed query works", async ({ page }: { page: Page }) => {
			const button = page.getByTestId("apollo-delayed-query-button");
			await button.scrollIntoViewIfNeeded();
			await button.click();

			// Verify the result
			const result = page.getByTestId("apollo-delayed-query-result");
			await expect(result).toContainText('"hello": "Hello, world!"');
		});

		test("blog post with defer works", async ({ page }: { page: Page }) => {
			const button = page.getByTestId("apollo-defer-button");
			await button.scrollIntoViewIfNeeded();
			await button.click();

			// Verify initial data loads
			const result = page.getByTestId("apollo-defer-result");
			await expect(result).toContainText('"title":');
			await expect(result).toContainText('"content":');

			// Verify deferred comments load
			await expect(result).toContainText('"comments":');
		});
	});

	test.describe("Relay Tests", () => {
		test("basic query works", async ({ page }: { page: Page }) => {
			const button = page.getByTestId("relay-basic-query-button");
			await button.scrollIntoViewIfNeeded();
			await button.click();

			// Verify the exact result
			const result = page.getByTestId("relay-basic-query-result");
			await expect(result).toContainText('"hello": "Hello, world!"');
		});

		test("delayed query works", async ({ page }: { page: Page }) => {
			const button = page.getByTestId("relay-delayed-query-button");
			await button.scrollIntoViewIfNeeded();
			await button.click();

			// Verify the result
			const result = page.getByTestId("relay-delayed-query-result");
			await expect(result).toContainText('"hello": "Hello, world!"');
		});

		test("blog post with defer works", async ({ page }: { page: Page }) => {
			const button = page.getByTestId("relay-defer-button");
			await button.scrollIntoViewIfNeeded();
			await button.click();

			// Verify initial data loads
			const result = page.getByTestId("relay-defer-result");
			await expect(result).toContainText('"title":');
			await expect(result).toContainText('"content":');

			// Verify deferred comments load in fragment
			const comments = page.getByTestId("relay-defer-comments");
			await expect(comments).toContainText('"comments":');
		});

		test("error boundary catches errors", async ({ page }: { page: Page }) => {
			// Force an error by manipulating network conditions
			await page.route("**/graphql", async (route) => {
				await route.abort();
			});

			const button = page.getByTestId("relay-basic-query-button");
			await button.scrollIntoViewIfNeeded();
			await button.click();

			// Verify error boundary catches and displays error
			await expect(page.getByTestId("error-boundary-message")).toBeVisible();
			await expect(
				page.getByTestId("error-boundary-refresh-message"),
			).toBeVisible();
		});
	});
});
