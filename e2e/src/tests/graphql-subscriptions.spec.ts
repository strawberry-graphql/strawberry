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

	test("websocket query renders a single result", async ({ page }) => {
		await page.goto("/ws");
		await page.getByTestId("ws-query-button").click();

		const result = page.getByTestId("ws-query-result");
		await expect(result).toContainText('"hello": "Hello, world!"');
		await expect(page.getByTestId("ws-query-status")).toContainText("complete");
		await expect(page.getByTestId("ws-query-error")).toHaveCount(0);
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
});
