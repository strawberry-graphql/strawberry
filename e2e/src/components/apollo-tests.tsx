import { gql, useQuery } from "@apollo/client";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const HELLO_QUERY = gql`
	query GetHello($delay: Float) {
		hello(delay: $delay)
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

interface ApolloQueryWrapperProps {
	query: typeof HELLO_QUERY;
	// biome-ignore lint/suspicious/noExplicitAny: typing this would be a pain
	variables?: any;
	buttonText?: string;
	testId?: string;
}

function ApolloQueryWrapper({
	query,
	variables,
	buttonText = "Run Query",
	testId,
}: ApolloQueryWrapperProps) {
	const [shouldRun, setShouldRun] = useState(false);

	const { data, loading, error } = useQuery(query, {
		variables,
		skip: !shouldRun,
		fetchPolicy: "network-only",
	});

	if (!shouldRun) {
		return (
			<Button
				onClick={() => setShouldRun(true)}
				data-testid={`${testId}-button`}
			>
				{buttonText}
			</Button>
		);
	}

	if (loading) return <p data-testid={`${testId}-loading`}>Loading...</p>;
	if (error)
		return <p data-testid={`${testId}-error`}>Error: {error.message}</p>;

	return (
		<pre data-testid={`${testId}-result`}>{JSON.stringify(data, null, 2)}</pre>
	);
}

function ApolloTests() {
	return (
		<div className="flex flex-col gap-4">
			<h1 className="text-2xl font-bold">Apollo Tests</h1>
			<div className=" gap-4">
				<h2 className="text-lg"># Basic Query</h2>
				<ApolloQueryWrapper query={HELLO_QUERY} testId="apollo-basic-query" />
			</div>
			<div className=" gap-4">
				<h2 className="text-lg"># Hello With Delay</h2>
				<ApolloQueryWrapper
					query={HELLO_QUERY}
					variables={{ delay: 2 }}
					testId="apollo-delayed-query"
				/>
			</div>
			<div className="gap-4">
				<h2 className="text-lg"># Blog Post</h2>
				<ApolloQueryWrapper
					query={BLOG_POST_QUERY}
					variables={{ id: "1" }}
					testId="apollo-blog-post"
				/>
			</div>
			<div className="gap-4">
				<h2 className="text-lg"># Blog Post With Defer</h2>
				<ApolloQueryWrapper
					query={BLOG_POST_QUERY}
					variables={{ shouldDefer: true, id: "1" }}
					testId="apollo-defer"
				/>
			</div>
		</div>
	);
}

export default ApolloTests;
