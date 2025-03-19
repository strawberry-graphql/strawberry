import { graphql, useLazyLoadQuery } from "react-relay";
import { Button } from "@/components/ui/button";
import { Suspense, useState } from "react";

const HELLO_QUERY = graphql`
  query relayTestsHelloQuery($delay: Float = 0) {
    hello(delay: $delay)
  }
`;

const COMMENTS_FRAGMENT = graphql`
  fragment relayTestsCommentsFragment on BlogPost {
    comments {
      id
      content
    }
  }
`;

const BLOG_POST_QUERY = graphql`
  query relayTestsBlogPostQuery($id: ID!, $shouldDefer: Boolean = false) {
    blogPost(id: $id) {
      title
      content
      ...relayTestsCommentsFragment @defer(if: $shouldDefer)
    }
  }
`;

interface RelayQueryWrapperProps {
	query: typeof HELLO_QUERY;
	// biome-ignore lint/suspicious/noExplicitAny: typing this would be a pain
	variables?: any;
	buttonText?: string;
}

function RelayFetchQuery({ query, variables }: RelayQueryWrapperProps) {
	const data = useLazyLoadQuery(query, variables ?? {});
	return <pre>{JSON.stringify(data, null, 2)}</pre>;
}

function RelayQueryWrapper({
	query,
	variables,
	buttonText = "Run Query",
}: RelayQueryWrapperProps) {
	const [shouldRun, setShouldRun] = useState(false);

	if (!shouldRun) {
		return <Button onClick={() => setShouldRun(true)}>{buttonText}</Button>;
	}

	return (
		<Suspense fallback={<div>Loading...</div>}>
			<RelayFetchQuery query={query} variables={variables} />
		</Suspense>
	);
}

function RelayTests() {
	return (
		<div className="flex flex-col gap-4">
			<h1 className="text-2xl font-bold">Relay Tests</h1>
			<div className="gap-4">
				<h2 className="text-lg"># Basic Query</h2>
				<RelayQueryWrapper query={HELLO_QUERY} />
			</div>
			<div className="gap-4">
				<h2 className="text-lg"># Hello With Delay</h2>
				<RelayQueryWrapper query={HELLO_QUERY} variables={{ delay: 2 }} />
			</div>
			<div className="gap-4">
				<h2 className="text-lg"># Blog Post</h2>
				<RelayQueryWrapper query={BLOG_POST_QUERY} variables={{ id: "1" }} />
			</div>
			<div className="gap-4">
				<h2 className="text-lg"># Blog Post With Defer</h2>
				<RelayQueryWrapper
					query={BLOG_POST_QUERY}
					variables={{ id: "1", shouldDefer: true }}
				/>
			</div>
		</div>
	);
}

export default RelayTests;
