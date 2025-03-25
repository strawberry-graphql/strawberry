import { serializeFetchParameter } from "@apollo/client";
import type { CacheConfig, RequestParameters } from "relay-runtime";
import {
	Environment,
	Network,
	Observable,
	RecordSource,
	Store,
	QueryResponseCache,
} from "relay-runtime";
import type { Variables } from "relay-runtime";
import { maybe } from "@apollo/client/utilities";
import {
	handleError,
	readMultipartBody,
} from "@apollo/client/link/http/parseAndCheckHttpResponse";

const uri = "http://localhost:8000/graphql";

const oneMinute = 60 * 1000;
const cache = new QueryResponseCache({ size: 250, ttl: oneMinute });

const backupFetch = maybe(() => fetch);

function fetchQuery(
	operation: RequestParameters,
	variables: Variables,
	cacheConfig: CacheConfig,
) {
	const queryID = operation.text;
	const isMutation = operation.operationKind === "mutation";
	const isQuery = operation.operationKind === "query";
	const forceFetch = cacheConfig && cacheConfig.force;

	// Try to get data from cache on queries
	const fromCache = cache.get(queryID, variables);
	if (isQuery && fromCache !== null && !forceFetch) {
		return fromCache;
	}

	const body = {
		operationName: operation.name,
		variables,
		query: operation.text || "",
	};

	const options: {
		method: string;
		headers: Record<string, any>;
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
			options.body = serializeFetchParameter(body, "Payload");
		} catch (parseError) {
			sink.error(parseError as Error);
		}

		const currentFetch = maybe(() => fetch) || backupFetch;

		const observerNext = (data) => {
			if ("incremental" in data) {
				for (const item of data.incremental) {
					sink.next(item);
				}
			} else if ("data" in data) {
				sink.next(data);
			}
		};

		currentFetch!(uri, options)
			.then(async (response) => {
				const ctype = response.headers?.get("content-type");

				if (ctype !== null && /^multipart\/mixed/i.test(ctype)) {
					const result = readMultipartBody(response, observerNext);
					console.log("result", result);
					return result;
				} else {
					const json = await response.json();

					if (isQuery && json) {
						cache.set(queryID, variables, json);
					}
					// Clear cache on mutations
					if (isMutation) {
						cache.clear();
					}

					observerNext(json);
				}
			})
			.then(() => {
				sink.complete();
			})
			.catch((err: any) => {
				handleError(err, sink);
			});
	});
}

const network = Network.create(fetchQuery);

export const RelayEnvironment = new Environment({
	network,
	store: new Store(new RecordSource()),
});
