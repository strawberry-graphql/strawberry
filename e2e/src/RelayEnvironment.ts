import type { RequestParameters } from "relay-runtime";
import {
	Environment,
	Network,
	Observable,
	RecordSource,
	Store,
} from "relay-runtime";
import type { Variables } from "relay-runtime";

const uri = "http://localhost:8000/graphql";

/**
 * Parse a multipart/mixed response body for GraphQL defer support.
 * This handles the incremental delivery format used by @defer directives.
 */
async function readMultipartBody<T extends object>(
	response: Response,
	nextValue: (value: T) => void,
): Promise<void> {
	const contentType = response.headers.get("content-type") || "";
	const boundaryMatch = contentType.match(/boundary=([^;]+)/i);
	const boundary = boundaryMatch ? boundaryMatch[1].trim() : "-";

	const reader = response.body?.getReader();
	if (!reader) {
		throw new Error("Response body is not readable");
	}

	const decoder = new TextDecoder();
	let buffer = "";

	while (true) {
		const { done, value } = await reader.read();

		if (done) {
			break;
		}

		buffer += decoder.decode(value, { stream: true });

		// Process complete parts from the buffer
		const parts = buffer.split(`--${boundary}`);
		// Keep the last part in the buffer (it might be incomplete)
		buffer = parts.pop() || "";

		for (const part of parts) {
			// Skip empty parts and the closing boundary
			if (!part.trim() || part.trim() === "--") {
				continue;
			}

			// Find the JSON content in the part (after headers)
			const headerBodySplit = part.indexOf("\r\n\r\n");
			if (headerBodySplit === -1) {
				continue;
			}

			const body = part.substring(headerBodySplit + 4).trim();
			if (!body) {
				continue;
			}

			try {
				const json = JSON.parse(body) as T;
				nextValue(json);
			} catch {
				// Skip invalid JSON parts
			}
		}
	}

	// Process any remaining content in the buffer
	if (buffer.trim() && buffer.trim() !== "--") {
		const headerBodySplit = buffer.indexOf("\r\n\r\n");
		if (headerBodySplit !== -1) {
			const body = buffer.substring(headerBodySplit + 4).trim();
			if (body) {
				try {
					const json = JSON.parse(body) as T;
					nextValue(json);
				} catch {
					// Skip invalid JSON
				}
			}
		}
	}
}

function fetchQuery(operation: RequestParameters, variables: Variables) {
	const body = {
		operationName: operation.name,
		variables,
		query: operation.text || "",
	};

	const options: {
		method: string;
		headers: Record<string, string>;
		body?: string;
	} = {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			accept: "multipart/mixed;deferSpec=20220824,application/json",
		},
	};

	return Observable.create((sink) => {
		try {
			options.body = JSON.stringify(body);
		} catch (parseError) {
			sink.error(parseError as Error);
		}

		// biome-ignore lint/suspicious/noExplicitAny: :)
		const observerNext = (data: any) => {
			console.log("data", data);
			if ("incremental" in data) {
				for (const item of data.incremental) {
					sink.next(item);
				}
			} else if ("data" in data) {
				sink.next(data);
			}
		};

		fetch(uri, options)
			.then(async (response: Response) => {
				console.log("response", response);

				const ctype = response.headers?.get("content-type");

				if (ctype !== null && /^multipart\/mixed/i.test(ctype)) {
					return readMultipartBody(response, observerNext);
				}

				const json = await response.json();

				console.log("json", json);

				observerNext(json);
			})
			.then(() => {
				sink.complete();
			})
			.catch((err: Error) => {
				sink.error(err);
			});
	});
}

const network = Network.create(fetchQuery);

export const RelayEnvironment = new Environment({
	network,
	store: new Store(new RecordSource()),
});
