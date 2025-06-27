import { ApolloClient, InMemoryCache, ApolloProvider } from "@apollo/client";
import ApolloTests from "@/components/apollo-tests";
import { RelayEnvironmentProvider } from "react-relay";
import RelayTests from "./components/relay-tests";
import { RelayEnvironment } from "./RelayEnvironment";

const client = new ApolloClient({
	uri: "http://localhost:8000/graphql",
	cache: new InMemoryCache(),
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
