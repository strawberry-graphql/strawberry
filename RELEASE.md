---
release type: minor
---

This release adds support for Apollo Federation inline tracing (FTV1).

When a request includes the `apollo-federation-include-trace: ftv1` header, Strawberry now records per-resolver timing information and includes it in the response under `extensions.ftv1` as a base64-encoded protobuf message, following the [Apollo Federation trace format](https://www.apollographql.com/docs/federation/metrics/). This allows an Apollo Gateway to aggregate subgraph traces and report them to Apollo Studio.

Install the new optional extra to pull in the required `protobuf` dependency:

```shell
pip install 'strawberry-graphql[apollo-federation]'
```

Use the async extension for async schemas:

```python
import strawberry
from strawberry.extensions.tracing import ApolloFederationTracingExtension


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


schema = strawberry.Schema(
    query=Query,
    extensions=[ApolloFederationTracingExtension],
)
```

Or the sync version when running outside of an async context:

```python
from strawberry.extensions.tracing import ApolloFederationTracingExtensionSync

schema = strawberry.Schema(
    query=Query,
    extensions=[ApolloFederationTracingExtensionSync],
)
```

> **Security:** any client can send the `apollo-federation-include-trace: ftv1` header unless you restrict it. Tracing payloads expose resolver timing details, so make sure only a trusted Apollo Gateway (or other internal traffic) can request traces — for example by enforcing authentication, network policy, or stripping the header from public requests at the edge.
