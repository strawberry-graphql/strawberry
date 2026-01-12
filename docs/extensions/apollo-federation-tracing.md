---
title: Apollo Federation Tracing
summary: Add Apollo Federation inline tracing (FTV1) to your GraphQL server.
tags: tracing,federation
---

# `ApolloFederationTracingExtension`

This extension adds support for
[Apollo Federation inline tracing (FTV1)](https://www.apollographql.com/docs/federation/).
When a request includes the `apollo-federation-include-trace: ftv1` header, the
extension records per-resolver timing and includes the trace in the response as
a base64-encoded protobuf under `extensions.ftv1`.

<Note>

Make sure you have `protobuf` installed before using this extension.

```shell
pip install 'strawberry-graphql[apollo-federation]'
```

</Note>

## Usage example:

```python
import strawberry
from strawberry.extensions.tracing import ApolloFederationTracingExtension


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


schema = strawberry.Schema(
    Query,
    extensions=[
        ApolloFederationTracingExtension,
    ],
)
```

<Note>

If you are not running in an Async context then you'll need to use the sync
version:

```python
import strawberry
from strawberry.extensions.tracing import ApolloFederationTracingExtensionSync


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


schema = strawberry.Schema(
    Query,
    extensions=[
        ApolloFederationTracingExtensionSync,
    ],
)
```

</Note>

## API reference:

_No arguments_
