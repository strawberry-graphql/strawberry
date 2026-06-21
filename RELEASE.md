---
release type: minor
---

This release adds `Schema.stream(...)`, a shared execution API for custom
streaming integrations.

`Schema.stream(...)` accepts queries, mutations and subscriptions and always
returns an async sequence of results: a single `ExecutionResult` for queries and
mutations, and the stream of results for subscriptions. This lets streaming
transports use one schema entry point instead of choosing between `execute` and
`subscribe` themselves.

Incremental delivery operations (`@defer`/`@stream`) are also supported: their
initial result is yielded first, followed by each raw graphql-core patch frame,
which the transport is responsible for formatting.

The schema execution APIs accept either a string or an already-parsed
`DocumentNode`, so a transport that parsed the document itself (for example to
inspect the operation type before executing) can pass the node to avoid parsing
it again.

Strawberry's multipart HTTP transport and `graphql-transport-ws` handler now use
this path internally.

HTTP multipart response framing now lives in the stream transport layer instead
of `AsyncBaseHTTPView.encode_multipart_data`. Integrations that customized that
view method should customize the transport encoding instead.
