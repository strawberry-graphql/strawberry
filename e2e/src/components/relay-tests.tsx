import { graphql, useLazyLoadQuery, useFragment } from "react-relay";
import { Button } from "@/components/ui/button";
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
}: {
	fragment: typeof COMMENTS_FRAGMENT;
	data: any;
}) {
	const fragmentData = useFragment(fragment, data);

	return <pre>{JSON.stringify(fragmentData, null, 2)}</pre>;
}

function RelayFetchQuery({
	query,
	variables,
	fragment,
}: RelayQueryWrapperProps) {
	const data = useLazyLoadQuery(query, variables ?? {});
	const filteredData = filterData(data);

	return (
		<>
			<pre>{JSON.stringify(filteredData, null, 2)}</pre>
			<Suspense fallback={<div>Loading fragment...</div>}>
				{fragment && data ? (
					<RelayFragmentWrapper fragment={fragment} data={data.blogPost} />
				) : null}
			</Suspense>
		</>
	);
}

function RelayQueryWrapper({
	query,
	variables,
	buttonText = "Run Query",
	fragment,
}: RelayQueryWrapperProps) {
	const [shouldRun, setShouldRun] = useState(false);

	if (!shouldRun) {
		return <Button onClick={() => setShouldRun(true)}>{buttonText}</Button>;
	}

	return (
		<Suspense fallback={<div>Loading...</div>}>
			<RelayFetchQuery
				query={query}
				variables={variables}
				fragment={fragment}
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
				<div className="p-4 border border-red-500 rounded-md bg-red-50">
					<h2 className="text-red-700 font-bold">Something went wrong.</h2>
					<p className="text-red-600">Please try refreshing the page.</p>
					{this.state.error && (
						<pre className="mt-4 p-2 bg-red-100 rounded text-sm overflow-auto">
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
					<RelayQueryWrapper
						query={BLOG_POST_QUERY}
						variables={{ id: "1" }}
						fragment={COMMENTS_FRAGMENT}
					/>
				</div>
				<div className="gap-4">
					<h2 className="text-lg"># Blog Post With Defer</h2>
					<RelayQueryWrapper
						query={BLOG_POST_QUERY}
						variables={{ id: "1", shouldDefer: true }}
						fragment={COMMENTS_FRAGMENT}
					/>
				</div>
			</div>
		</ErrorBoundary>
	);
}

export default RelayTests;
