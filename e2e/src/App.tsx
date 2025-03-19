import { ApolloClient, InMemoryCache, ApolloProvider } from "@apollo/client";
import ApolloTests from "@/components/apollo-tests";

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
			<main className="p-4">
				<ApolloProvider client={client}>
					<ApolloTests />
				</ApolloProvider>
			</main>
		</div>
	);
}

export default App;
