import { expect, test } from "@playwright/test";

// SSE reconnection is exercised at the HTTP level: a reconnecting client sends
// the id of the last event it saw in the `Last-Event-ID` header, which the
// resolver reads from `info.context["last_event_id"]` to resume. (The graphql-sse
// React client cannot drive this in distinct connections mode.)
test.describe("GraphQL SSE reconnection", () => {
	const query = "subscription { resumableCount(target: 3) }";

	// The `complete` event carries an empty data field, so only `data: {` lines
	// hold a result.
	const streamedCounts = (body: string) =>
		body
			.split("\r\n")
			.filter((line) => line.startsWith("data: {"))
			.map(
				(line) => JSON.parse(line.slice("data: ".length)).data.resumableCount,
			);

	test("streams all results without Last-Event-ID", async ({ request }) => {
		const response = await request.post("/graphql", {
			headers: { accept: "text/event-stream" },
			data: { query },
		});

		expect(response.status()).toBe(200);
		expect(response.headers()["content-type"]).toContain("text/event-stream");

		const body = await response.text();
		expect(streamedCounts(body)).toEqual([0, 1, 2]);
	});

	test("resumes from the Last-Event-ID header", async ({ request }) => {
		const response = await request.post("/graphql", {
			headers: { accept: "text/event-stream", "last-event-id": "1" },
			data: { query },
		});

		expect(response.status()).toBe(200);

		const body = await response.text();
		// Resumes after id 1: the already-seen results are not replayed.
		expect(streamedCounts(body)).toEqual([2]);
	});
});
