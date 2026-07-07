import {
	ApolloClient,
	gql,
	HttpLink,
	InMemoryCache,
} from "@apollo/client/core";
import { useMutation, useQuery } from "@apollo/client/react";
import { Button } from "@/components/ui/button";
import {
	ErrorBanner,
	Icons,
	LoadingRow,
	ResultBlock,
	TestCard,
} from "@/components/test-ui";
import { useState } from "react";

const HELLO_QUERY = gql`
	query GetHello($delay: Float) {
		hello(delay: $delay)
	}
`;

const FAILING_QUERY = gql`
	query GetFailing {
		failing
	}
`;

const ECHO_MUTATION = gql`
	mutation Echo($message: String!) {
		echo(message: $message)
	}
`;

const BLOG_POST_QUERY = gql`
	query GetBlogPost($id: ID!, $shouldDefer: Boolean) {
		blogPost(id: $id) {
			title
			content
			... CommentsFragment @defer(if: $shouldDefer)
		}
	}
	fragment CommentsFragment on BlogPost {
		comments {
			id
			content
		}
	}
`;

// Apollo client that sends queries over GET (mutations still use POST).
const getApolloClient = new ApolloClient({
	link: new HttpLink({ uri: "/graphql", useGETForQueries: true }),
	cache: new InMemoryCache(),
});

interface ApolloQueryWrapperProps {
	query: typeof HELLO_QUERY;
	// biome-ignore lint/suspicious/noExplicitAny: typing this would be a pain
	variables?: any;
	buttonText?: string;
	testId?: string;
	client?: ApolloClient;
}

function ApolloQueryWrapper({
	query,
	variables,
	buttonText = "Run Query",
	testId,
	client,
}: ApolloQueryWrapperProps) {
	const [shouldRun, setShouldRun] = useState(false);

	const { data, loading, error } = useQuery(query, {
		variables,
		skip: !shouldRun,
		fetchPolicy: "network-only",
		client,
	});

	if (!shouldRun) {
		return (
			<Button
				onClick={() => setShouldRun(true)}
				data-testid={`${testId}-button`}
				className="self-start"
			>
				{buttonText}
			</Button>
		);
	}

	if (error)
		return <ErrorBanner message={error.message} testId={`${testId}-error`} />;

	if (data)
		return (
			<ResultBlock testId={`${testId}-result`}>
				{JSON.stringify(data, null, 2)}
			</ResultBlock>
		);

	if (loading) return <LoadingRow testId={`${testId}-loading`} />;
}

function ApolloMutationWrapper({ testId }: { testId?: string }) {
	const [runMutation, { data, loading, error }] = useMutation(ECHO_MUTATION);

	return (
		<>
			<Button
				onClick={() => void runMutation({ variables: { message: "hello there" } })}
				disabled={loading}
				data-testid={`${testId}-button`}
				className="self-start"
			>
				Run Mutation
			</Button>
			{error && <ErrorBanner message={error.message} testId={`${testId}-error`} />}
			{data && (
				<ResultBlock testId={`${testId}-result`}>
					{JSON.stringify(data, null, 2)}
				</ResultBlock>
			)}
		</>
	);
}

function ApolloTests() {
	return (
		<div className="flex flex-col gap-6">
			<div className="flex items-center gap-2">
				<h2 className="font-display text-2xl font-bold tracking-tight">
					Apollo
				</h2>
				<span className="rounded-full bg-g-50 px-2.5 py-0.5 text-xs font-bold text-g-700">
					HTTP
				</span>
			</div>
			<div className="flex flex-col gap-4">
				<TestCard title="Basic Query" icon={Icons.bolt}>
					<ApolloQueryWrapper query={HELLO_QUERY} testId="apollo-basic-query" />
				</TestCard>
				<TestCard title="Query Over GET" icon={Icons.bolt}>
					<ApolloQueryWrapper
						query={HELLO_QUERY}
						client={getApolloClient}
						testId="apollo-get-query"
					/>
				</TestCard>
				<TestCard title="Mutation" icon={Icons.bolt}>
					<ApolloMutationWrapper testId="apollo-mutation" />
				</TestCard>
				<TestCard title="Query Error" icon={Icons.bolt}>
					<ApolloQueryWrapper query={FAILING_QUERY} testId="apollo-error-query" />
				</TestCard>
				<TestCard title="Hello With Delay" icon={Icons.bolt}>
					<ApolloQueryWrapper
						query={HELLO_QUERY}
						variables={{ delay: 2 }}
						testId="apollo-delayed-query"
					/>
				</TestCard>
				<TestCard title="Blog Post" icon={Icons.database}>
					<ApolloQueryWrapper
						query={BLOG_POST_QUERY}
						variables={{ id: "1" }}
						testId="apollo-blog-post"
					/>
				</TestCard>
				<TestCard title="Blog Post With Defer" icon={Icons.database}>
					<ApolloQueryWrapper
						query={BLOG_POST_QUERY}
						variables={{ shouldDefer: true, id: "1" }}
						testId="apollo-defer"
					/>
				</TestCard>
			</div>
		</div>
	);
}

export default ApolloTests;
