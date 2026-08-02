import {
	ApolloClient,
	ApolloLink,
	gql,
	InMemoryCache,
	Observable,
} from "@apollo/client/core";
import { GraphQLWsLink } from "@apollo/client/link/subscriptions";
import { useLazyQuery, useSubscription } from "@apollo/client/react";
import { print, type DocumentNode } from "graphql";
import {
	type Client as GraphQLSSEClient,
	type ClientOptions as GraphQLSSEClientOptions,
	createClient as createSSEClient,
} from "graphql-sse";
import { createClient as createWsClient } from "graphql-ws";
import { type ReactNode, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
	ErrorBanner,
	Icons,
	ResultBlock,
	StatusBadge,
	TestCard,
} from "@/components/test-ui";

const GRAPHQL_URL = "/graphql";
const COUNT_SUBSCRIPTION = gql`
	subscription CountSubscription {
		count(target: 2)
	}
`;
const COUNT_THEN_FAIL_SUBSCRIPTION = gql`
	subscription CountThenFailSubscription {
		countThenFail(target: 2)
	}
`;
const HELLO_QUERY = gql`
	query WsHelloQuery {
		hello
	}
`;

type CountData = { count?: number; countThenFail?: number };
type HelloData = { hello: string };
type RunStatus = "idle" | "loading" | "complete";

function getErrorMessage(error: unknown) {
	return error instanceof Error ? error.message : String(error);
}

function getWebsocketGraphqlUrl() {
	const url = new URL(GRAPHQL_URL, window.location.href);
	url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
	return url.toString();
}

class SSELink extends ApolloLink {
	private readonly client: GraphQLSSEClient;

	constructor(options: GraphQLSSEClientOptions) {
		super();
		this.client = createSSEClient(options);
	}

	override request(operation: ApolloLink.Operation) {
		return new Observable<ApolloLink.Result>((sink) => {
			return this.client.subscribe(
				{
					operationName: operation.operationName,
					query: print(operation.query),
					variables: operation.variables,
					extensions: operation.extensions,
				},
				{
					next: (result) => sink.next(result as ApolloLink.Result),
					error: (error) => sink.error(error),
					complete: () => sink.complete(),
				},
			);
		});
	}
}

const websocketApolloClient = new ApolloClient({
	link: new GraphQLWsLink(
		createWsClient({
			url: getWebsocketGraphqlUrl(),
			retryAttempts: 0,
		}),
	),
	cache: new InMemoryCache(),
});

const sseApolloClient = new ApolloClient({
	link: new SSELink({
		url: GRAPHQL_URL,
		retryAttempts: 0,
	}),
	cache: new InMemoryCache(),
});

interface ApolloSubscriptionTestProps {
	title: string;
	testId: string;
	subscription?: DocumentNode;
	client?: ApolloClient;
	icon?: ReactNode;
}

function ApolloSubscriptionTest({
	title,
	testId,
	subscription = COUNT_SUBSCRIPTION,
	client,
	icon,
}: ApolloSubscriptionTestProps) {
	const receivedCount = useRef(0);
	const [shouldRun, setShouldRun] = useState(false);
	const [results, setResults] = useState<CountData[]>([]);
	const [status, setStatus] = useState<RunStatus>("idle");
	const [error, setError] = useState<string | null>(null);

	useSubscription<CountData>(subscription, {
		client,
		skip: !shouldRun,
		fetchPolicy: "no-cache",
		shouldResubscribe: true,
		onData({ data }) {
			if (data.data) {
				const result = data.data as CountData;
				receivedCount.current += 1;
				setResults((currentResults) => [...currentResults, result]);
			}
		},
		onError(subscriptionError) {
			setError(getErrorMessage(subscriptionError));
			setStatus("idle");
			setShouldRun(false);
		},
		onComplete() {
			if (receivedCount.current > 0) {
				setStatus("complete");
			} else {
				setError("No subscription events received");
				setStatus("idle");
			}

			setShouldRun(false);
		},
	});

	function runSubscription() {
		receivedCount.current = 0;
		setResults([]);
		setError(null);
		setStatus("loading");
		setShouldRun(true);
	}

	return (
		<TestCard title={title} icon={icon}>
			<div className="flex flex-wrap items-center gap-3">
				<Button
					onClick={runSubscription}
					disabled={status === "loading"}
					data-testid={`${testId}-button`}
				>
					Run Subscription
				</Button>
				<StatusBadge
					status={error ? "error" : status}
					testId={`${testId}-status`}
				/>
			</div>
			{error && <ErrorBanner message={error} testId={`${testId}-error`} />}
			{results.length > 0 && (
				<ResultBlock testId={`${testId}-result`} label="count events">
					{JSON.stringify(results, null, 2)}
				</ResultBlock>
			)}
		</TestCard>
	);
}

function WebSocketQueryTest() {
	return (
		<SubscriptionQueryTest
			title="WebSocket Query"
			testId="ws-query"
			client={websocketApolloClient}
			icon={Icons.code}
		/>
	);
}

function SubscriptionQueryTest({
	title,
	testId,
	client,
	icon,
}: {
	title: string;
	testId: string;
	client: ApolloClient;
	icon?: ReactNode;
}) {
	const [runQuery, { data, loading, error }] = useLazyQuery<HelloData>(
		HELLO_QUERY,
		{
			client,
			fetchPolicy: "no-cache",
		},
	);
	const status: RunStatus = loading ? "loading" : data ? "complete" : "idle";

	return (
		<TestCard title={title} icon={icon}>
			<div className="flex flex-wrap items-center gap-3">
				<Button
					onClick={() => void runQuery()}
					disabled={loading}
					data-testid={`${testId}-button`}
				>
					Run Query
				</Button>
				<StatusBadge
					status={error ? "error" : status}
					testId={`${testId}-status`}
				/>
			</div>
			{error && (
				<ErrorBanner
					message={getErrorMessage(error)}
					testId={`${testId}-error`}
				/>
			)}
			{data && (
				<ResultBlock testId={`${testId}-result`} label="hello">
					{JSON.stringify(data, null, 2)}
				</ResultBlock>
			)}
		</TestCard>
	);
}

export function SSETests() {
	return (
		<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
			<ApolloSubscriptionTest
				title="SSE Subscription"
				testId="sse-subscription"
				client={sseApolloClient}
				icon={Icons.stream}
			/>
			<SubscriptionQueryTest
				title="SSE Query"
				testId="sse-query"
				client={sseApolloClient}
				icon={Icons.code}
			/>
			<ApolloSubscriptionTest
				title="SSE Subscription Error"
				testId="sse-failing-subscription"
				subscription={COUNT_THEN_FAIL_SUBSCRIPTION}
				client={sseApolloClient}
				icon={Icons.signal}
			/>
		</div>
	);
}

export function MultipartTests() {
	return (
		<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
			<ApolloSubscriptionTest
				title="Multipart Subscription"
				testId="multipart-subscription"
				icon={Icons.signal}
			/>
		</div>
	);
}

export function WebSocketTests() {
	return (
		<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
			<ApolloSubscriptionTest
				title="WebSocket Subscription"
				testId="websocket-subscription"
				client={websocketApolloClient}
				icon={Icons.plug}
			/>
			<WebSocketQueryTest />
			<ApolloSubscriptionTest
				title="WebSocket Subscription Error"
				testId="ws-failing-subscription"
				subscription={COUNT_THEN_FAIL_SUBSCRIPTION}
				client={websocketApolloClient}
				icon={Icons.signal}
			/>
		</div>
	);
}
