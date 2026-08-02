import { expect, test } from "@playwright/test";

// SSE reconnection is exercised at the HTTP level: a reconnecting client sends
// the id of the last event it saw in the `Last-Event-ID` header, which the
// resolver reads from `info.context["last_event_id"]` to resume. (The graphql-sse
// React client cannot drive this in distinct connections mode.)
test.describe("GraphQL SSE reconnection", () => {
	const query = "subscription { resumableCount(target: 3) }";

	test("streams all results without Last-Event-ID", async ({ request }) => {
		const response = await request.post("/graphql", {
			headers: { accept: "text/event-stream" },
			data: { query },
		});

		expect(response.status()).toBe(200);
		expect(response.headers()["content-type"]).toContain("text/event-stream");

		const body = await response.text();
		expect(body).toContain('"resumableCount": 0');
		expect(body).toContain('"resumableCount": 1');
		expect(body).toContain('"resumableCount": 2');
	});

	test("resumes from the Last-Event-ID header", async ({ request }) => {
		const response = await request.post("/graphql", {
			headers: { accept: "text/event-stream", "last-event-id": "1" },
			data: { query },
		});

		expect(response.status()).toBe(200);

		const body = await response.text();
		// Resumes after id 1: the already-seen results are not replayed.
		expect(body).not.toContain('"resumableCount": 0');
		expect(body).not.toContain('"resumableCount": 1');
		expect(body).toContain('"resumableCount": 2');
	});
});
