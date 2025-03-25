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

const backupFetch = maybe(() => fetch);

function fetchQuery(operation: RequestParameters, variables: Variables) {
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
			console.log("data", data);
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
				console.log("response", response);

				const ctype = response.headers?.get("content-type");

				if (ctype !== null && /^multipart\/mixed/i.test(ctype)) {
					const result = readMultipartBody(response, observerNext);

					return result;
				}

				const json = await response.json();

				console.log("json", json);

				observerNext(json);
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
