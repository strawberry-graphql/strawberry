import { ApolloClient, InMemoryCache, HttpLink } from "@apollo/client/core";
import { Defer20220824Handler } from "@apollo/client/incremental";
import { ApolloProvider } from "@apollo/client/react";
import ApolloTests from "@/components/apollo-tests";
import {
	MultipartTests,
	SSETests,
	WebSocketTests,
} from "@/components/subscription-tests";
import { RelayEnvironmentProvider } from "react-relay";
import RelayTests, { RelaySSETests } from "./components/relay-tests";
import { RelayEnvironment, RelaySSEEnvironment } from "./RelayEnvironment";

const client = new ApolloClient({
	link: new HttpLink({ uri: "/graphql" }),
	cache: new InMemoryCache(),
	// Enable @defer support with the 2022-08-24 defer spec
	incrementalHandler: new Defer20220824Handler(),
});

const NAV_ITEMS = [
	{ href: "/", label: "Home", testId: "home-link" },
	{ href: "/multipart", label: "Multipart", testId: "multipart-link" },
	{ href: "/sse", label: "SSE", testId: "sse-link" },
	{ href: "/ws", label: "WS", testId: "websocket-link" },
] as const;

const PAGE_META: Record<string, { title: string; subtitle: string }> = {
	"/": {
		title: "Client integrations",
		subtitle: "Apollo & Relay — queries, delays, @defer and fragments.",
	},
	"/multipart": {
		title: "Multipart subscriptions",
		subtitle: "Streaming results over multipart HTTP responses.",
	},
	"/sse": {
		title: "SSE subscriptions",
		subtitle: "Streaming results over Server-Sent Events.",
	},
	"/ws": {
		title: "WebSocket subscriptions",
		subtitle: "Real-time results over the graphql-ws protocol.",
	},
};

function HomePage() {
	return (
		<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
			<ApolloTests />

			<RelayEnvironmentProvider environment={RelayEnvironment}>
				<RelayTests />
			</RelayEnvironmentProvider>
		</div>
	);
}

function SSEPage() {
	return (
		<div className="flex flex-col gap-10">
			<SSETests />

			<RelayEnvironmentProvider environment={RelaySSEEnvironment}>
				<RelaySSETests />
			</RelayEnvironmentProvider>
		</div>
	);
}

function App() {
	const path = window.location.pathname;
	const page =
		path === "/multipart" ? (
			<MultipartTests />
		) : path === "/sse" ? (
			<SSEPage />
		) : path === "/ws" ? (
			<WebSocketTests />
		) : (
			<HomePage />
		);

	const meta = PAGE_META[path] ?? PAGE_META["/"];

	return (
		<ApolloProvider client={client}>
			<div className="flex min-h-screen flex-col text-ink">
				<header className="sticky top-0 z-10 border-b border-g-100 bg-white/80 backdrop-blur-md">
					<div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 py-4">
						<a
							className="flex items-center gap-2 font-display text-xl font-bold tracking-tight"
							href="/"
						>
							<span className="text-2xl">🍓</span>
							<span>
								End&#8209;to&#8209;End{" "}
								<span className="gradient-text">Tests</span>
							</span>
						</a>
						<nav className="flex items-center gap-1 text-sm font-medium">
							{NAV_ITEMS.map((item) => {
								const isActive = path === item.href;
								return (
									<a
										key={item.href}
										href={item.href}
										data-testid={item.testId}
										aria-current={isActive ? "page" : undefined}
										className={
											isActive
												? "rounded-full bg-g-50 px-3 py-1.5 font-bold text-ink"
												: "rounded-full px-3 py-1.5 text-g-700 transition-colors hover:bg-g-50 hover:text-ink"
										}
									>
										{item.label}
									</a>
								);
							})}
						</nav>
					</div>
				</header>

				<main className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">
					<div className="mb-8 flex flex-col gap-1">
						<span className="text-xs font-bold uppercase tracking-widest text-strawberry">
							Strawberry GraphQL
						</span>
						<h1 className="font-display text-3xl font-bold tracking-tight md:text-4xl">
							{meta.title}
						</h1>
						<p className="text-g-700">{meta.subtitle}</p>
					</div>
					{page}
				</main>
			</div>
		</ApolloProvider>
	);
}

export default App;
