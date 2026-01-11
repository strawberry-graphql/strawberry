import { ApolloClient, InMemoryCache, HttpLink } from "@apollo/client/core";
import { Defer20220824Handler } from "@apollo/client/incremental";
import { ApolloProvider } from "@apollo/client/react";
import ApolloTests from "@/components/apollo-tests";
import { RelayEnvironmentProvider } from "react-relay";
import RelayTests from "./components/relay-tests";
import { RelayEnvironment } from "./RelayEnvironment";

const client = new ApolloClient({
	link: new HttpLink({ uri: "http://localhost:8000/graphql" }),
	cache: new InMemoryCache(),
	// Enable @defer support with the 2022-08-24 defer spec
	incrementalHandler: new Defer20220824Handler(),
});

function App() {
	return (
		<div className="flex flex-col gap-4 font-mono">
			<header className="text-2xl p-4 border-b border-black">
				🍓 End to End Tests
			</header>
			<main className="p-4 grid grid-cols-2">
				<ApolloProvider client={client}>
					<ApolloTests />
				</ApolloProvider>

				<RelayEnvironmentProvider environment={RelayEnvironment}>
					<RelayTests />
				</RelayEnvironmentProvider>
			</main>
		</div>
	);
}

export default App;
