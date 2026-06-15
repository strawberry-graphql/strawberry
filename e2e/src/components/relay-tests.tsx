import { graphql, useLazyLoadQuery, useFragment } from "react-relay";
import { Button } from "@/components/ui/button";
import {
	Icons,
	LoadingRow,
	ResultBlock,
	TestCard,
} from "@/components/test-ui";
import { Suspense, useState, Component } from "react";

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
	fragment?: typeof COMMENTS_FRAGMENT;
}

const filterData = (obj: unknown): unknown => {
	if (typeof obj !== "object" || obj === null) return obj;
	if (Array.isArray(obj)) return obj.map(filterData);
	return Object.fromEntries(
		Object.entries(obj as Record<string, unknown>)
			.filter(([key]) => !key.startsWith("__"))
			.map(([key, value]) => [key, filterData(value)]),
	);
};

// Add this type to help with TypeScript
type BlogPostQuery = {
	blogPost?: {
		title: string;
		content: string;
	};
};

function RelayFragmentWrapper({
	fragment,
	data,
	testId,
}: {
	fragment: typeof COMMENTS_FRAGMENT;
	data: any;
	testId?: string;
}) {
	const fragmentData = useFragment(fragment, data);

	return (
		<ResultBlock testId={testId} label="comments">
			{JSON.stringify(fragmentData, null, 2)}
		</ResultBlock>
	);
}

function RelayFetchQuery({
	query,
	variables,
	fragment,
	testId,
}: RelayQueryWrapperProps) {
	const data = useLazyLoadQuery(query, variables ?? {});
	const filteredData = filterData(data);

	return (
		<div className="flex flex-col gap-3">
			<ResultBlock testId={`${testId}-result`}>
				{JSON.stringify(filteredData, null, 2)}
			</ResultBlock>
			<Suspense
				fallback={
					<LoadingRow testId={`${testId}-fragment-loading`}>
						Loading fragment…
					</LoadingRow>
				}
			>
				{fragment && data ? (
					<RelayFragmentWrapper
						fragment={fragment}
						data={data.blogPost}
						testId={`${testId}-comments`}
					/>
				) : null}
			</Suspense>
		</div>
	);
}

function RelayQueryWrapper({
	query,
	variables,
	buttonText = "Run Query",
	fragment,
	testId,
}: RelayQueryWrapperProps & { testId?: string }) {
	const [shouldRun, setShouldRun] = useState(false);

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

	return (
		<Suspense fallback={<LoadingRow testId={`${testId}-loading`} />}>
			<RelayFetchQuery
				query={query}
				variables={variables}
				fragment={fragment}
				testId={testId}
			/>
		</Suspense>
	);
}

class ErrorBoundary extends Component<
	{ children: React.ReactNode },
	{ hasError: boolean; error: Error | null }
> {
	constructor(props: { children: React.ReactNode }) {
		super(props);
		this.state = { hasError: false, error: null };
	}

	static getDerivedStateFromError(error: Error) {
		return { hasError: true, error };
	}

	componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
		console.log(errorInfo.componentStack);
		console.error("Error caught by boundary:", error, errorInfo);
	}

	render() {
		if (this.state.hasError) {
			return (
				<div className="rounded-2xl border border-strawberry/30 bg-strawberry/5 p-5">
					<h2
						className="font-display text-lg font-bold text-strawberry"
						data-testid="error-boundary-message"
					>
						Something went wrong.
					</h2>
					<p
						className="mt-1 text-sm text-g-700"
						data-testid="error-boundary-refresh-message"
					>
						Please try refreshing the page.
					</p>
					{this.state.error && (
						<pre className="mt-4 overflow-auto rounded-xl bg-ink p-3 font-mono text-xs text-g-50">
							{this.state.error.stack}
						</pre>
					)}
				</div>
			);
		}

		return this.props.children;
	}
}

function RelayTests() {
	return (
		<ErrorBoundary>
			<div className="flex flex-col gap-6">
				<div className="flex items-center gap-2">
					<h2 className="font-display text-2xl font-bold tracking-tight">
						Relay
					</h2>
					<span className="rounded-full bg-g-50 px-2.5 py-0.5 text-xs font-bold text-g-700">
						HTTP
					</span>
				</div>
				<div className="flex flex-col gap-4">
					<TestCard title="Basic Query" icon={Icons.bolt}>
						<RelayQueryWrapper query={HELLO_QUERY} testId="relay-basic-query" />
					</TestCard>
					<TestCard title="Hello With Delay" icon={Icons.bolt}>
						<RelayQueryWrapper
							query={HELLO_QUERY}
							variables={{ delay: 2 }}
							testId="relay-delayed-query"
						/>
					</TestCard>
					<TestCard title="Blog Post" icon={Icons.layers}>
						<RelayQueryWrapper
							query={BLOG_POST_QUERY}
							variables={{ id: "1" }}
							fragment={COMMENTS_FRAGMENT}
							testId="relay-blog-post"
						/>
					</TestCard>
					<TestCard title="Blog Post With Defer" icon={Icons.layers}>
						<RelayQueryWrapper
							query={BLOG_POST_QUERY}
							variables={{ id: "1", shouldDefer: true }}
							fragment={COMMENTS_FRAGMENT}
							testId="relay-defer"
						/>
					</TestCard>
				</div>
			</div>
		</ErrorBoundary>
	);
}

export default RelayTests;
