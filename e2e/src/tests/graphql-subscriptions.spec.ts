import { expect, test } from "@playwright/test";

test.describe("GraphQL Subscription UI", () => {
	test("multipart subscription renders count events", async ({ page }) => {
		await page.goto("/multipart");
		await page.getByTestId("multipart-subscription-button").click();

		const result = page.getByTestId("multipart-subscription-result");
		await expect(result).toContainText('"count": 0');
		await expect(result).toContainText('"count": 1');
		await expect(
			page.getByTestId("multipart-subscription-status"),
		).toContainText("complete");
		await expect(page.getByTestId("multipart-subscription-error")).toHaveCount(0);
	});

	test("websocket subscription renders count events", async ({ page }) => {
		await page.goto("/ws");
		await page.getByTestId("websocket-subscription-button").click();

		const result = page.getByTestId("websocket-subscription-result");
		await expect(result).toContainText('"count": 0');
		await expect(result).toContainText('"count": 1');
		await expect(page.getByTestId("websocket-subscription-status")).toContainText(
			"complete",
		);
		await expect(page.getByTestId("websocket-subscription-error")).toHaveCount(0);
	});

	test("sse subscription renders count events", async ({ page }) => {
		await page.goto("/sse");

		const sseRequest = page.waitForRequest((request) => {
			return (
				request.url().includes("/graphql") &&
				request.headers()["accept"] === "text/event-stream"
			);
		});

		await page.getByTestId("sse-subscription-button").click();
		await sseRequest;

		const result = page.getByTestId("sse-subscription-result");
		await expect(result).toContainText('"count": 0');
		await expect(result).toContainText('"count": 1');
		await expect(page.getByTestId("sse-subscription-status")).toContainText(
			"complete",
		);
		await expect(page.getByTestId("sse-subscription-error")).toHaveCount(0);
	});

	test("websocket query renders a single result", async ({ page }) => {
		await page.goto("/ws");
		await page.getByTestId("ws-query-button").click();

		const result = page.getByTestId("ws-query-result");
		await expect(result).toContainText('"hello": "Hello, world!"');
		await expect(page.getByTestId("ws-query-status")).toContainText("complete");
		await expect(page.getByTestId("ws-query-error")).toHaveCount(0);
	});

	test("sse query renders a single result", async ({ page }) => {
		await page.goto("/sse");

		const sseRequest = page.waitForRequest((request) => {
			return (
				request.url().includes("/graphql") &&
				request.headers()["accept"] === "text/event-stream"
			);
		});

		await page.getByTestId("sse-query-button").click();
		await sseRequest;

		const result = page.getByTestId("sse-query-result");
		await expect(result).toContainText('"hello": "Hello, world!"');
		await expect(page.getByTestId("sse-query-status")).toContainText("complete");
		await expect(page.getByTestId("sse-query-error")).toHaveCount(0);
	});

	test("relay sse query renders a single result", async ({ page }) => {
		await page.goto("/sse");

		const sseRequest = page.waitForRequest((request) => {
			return (
				request.url().includes("/graphql") &&
				request.headers()["accept"] === "text/event-stream"
			);
		});

		await page.getByTestId("relay-sse-query-button").click();
		await sseRequest;

		const result = page.getByTestId("relay-sse-query-result");
		await expect(result).toContainText('"hello": "Hello, world!"');
	});

	test("relay sse subscription renders count events", async ({ page }) => {
		await page.goto("/sse");

		const sseRequest = page.waitForRequest((request) => {
			return (
				request.url().includes("/graphql") &&
				request.headers()["accept"] === "text/event-stream"
			);
		});

		await page.getByTestId("relay-sse-subscription-button").click();
		await sseRequest;

		const result = page.getByTestId("relay-sse-subscription-result");
		await expect(result).toContainText('"count": 0');
		await expect(result).toContainText('"count": 1');
		await expect(page.getByTestId("relay-sse-subscription-status")).toContainText(
			"complete",
		);
		await expect(page.getByTestId("relay-sse-subscription-error")).toHaveCount(0);
	});

	test("websocket subscription surfaces a mid-stream error", async ({ page }) => {
		await page.goto("/ws");
		await page.getByTestId("ws-failing-subscription-button").click();

		// streams a couple of events, then the resolver raises server-side
		await expect(
			page.getByTestId("ws-failing-subscription-result"),
		).toContainText('"countThenFail": 0');
		await expect(
			page.getByTestId("ws-failing-subscription-error"),
		).toBeVisible();
	});

	test("sse subscription surfaces a mid-stream error", async ({ page }) => {
		await page.goto("/sse");
		await page.getByTestId("sse-failing-subscription-button").click();

		await expect(
			page.getByTestId("sse-failing-subscription-result"),
		).toContainText('"countThenFail": 0');
		await expect(
			page.getByTestId("sse-failing-subscription-error"),
		).toBeVisible();
	});

	test("relay sse subscription surfaces a mid-stream error", async ({ page }) => {
		await page.goto("/sse");
		await page.getByTestId("relay-sse-failing-subscription-button").click();

		await expect(
			page.getByTestId("relay-sse-failing-subscription-result"),
		).toContainText('"countThenFail": 0');
		await expect(
			page.getByTestId("relay-sse-failing-subscription-error"),
		).toBeVisible();
	});
});
