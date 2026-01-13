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
 * Based on Apollo Client's implementation.
 */
async function readMultipartBody<T extends object>(
	response: Response,
	nextValue: (value: T) => void,
): Promise<void> {
	const decoder = new TextDecoder("utf-8");
	const contentType = response.headers?.get("content-type") || "";

	// Parse boundary value from content-type header
	// e.g. multipart/mixed;boundary="graphql";deferSpec=20220824
	const match = contentType.match(
		/;\s*boundary=(?:'([^']+)'|"([^"]+)"|([^"'].+?))\s*(?:;|$)/i,
	);
	const boundary =
		"\r\n--" + (match ? (match[1] ?? match[2] ?? match[3] ?? "-") : "-");

	const reader = response.body?.getReader();
	if (!reader) {
		throw new Error("Response body is not readable");
	}

	let buffer = "";
	let done = false;
	let encounteredBoundary = false;

	// Check if we've passed the final boundary (boundary followed by --)
	const passedFinalBoundary = () =>
		encounteredBoundary && buffer[0] === "-" && buffer[1] === "-";

	try {
		while (!done) {
			const result = await reader.read();
			done = result.done;
			const chunk =
				typeof result.value === "string"
					? result.value
					: decoder.decode(result.value);

			const searchFrom = buffer.length - boundary.length + 1;
			buffer += chunk;

			let bi = buffer.indexOf(boundary, searchFrom);

			while (bi > -1 && !passedFinalBoundary()) {
				encounteredBoundary = true;

				const message = buffer.slice(0, bi);
				buffer = buffer.slice(bi + boundary.length);

				// Find the header/body separator
				const i = message.indexOf("\r\n\r\n");
				if (i > -1) {
					// The body is after the headers (slice includes leading \r\n but JSON.parse handles it)
					const body = message.slice(i);
					if (body) {
						try {
							const result = JSON.parse(body) as T;
							// Skip empty objects
							if (Object.keys(result).length > 0) {
								// Handle Apollo-style payload wrapper if present
								if (
									typeof result === "object" &&
									result !== null &&
									"payload" in result
								) {
									const payloadResult = result as { payload: T | null };
									if (payloadResult.payload !== null) {
										nextValue(payloadResult.payload as T);
									}
								} else {
									nextValue(result);
								}
							}
						} catch {
							// Skip invalid JSON
						}
					}
				}

				bi = buffer.indexOf(boundary);
			}

			if (passedFinalBoundary()) {
				return;
			}
		}
	} finally {
		reader.cancel();
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
