---
title: Apollo Tracing
summary: Add Apollo tracing to your GraphQL server.
tags: tracing
---

# `ApolloTracingExtension`

This extension adds
[tracing information](https://github.com/apollographql/apollo-tracing) to your
response for [Apollo Engine](https://www.apollographql.com/platform/).

## Usage example:

```python
import strawberry
from strawberry.extensions.tracing import ApolloTracingExtension


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


schema = strawberry.Schema(
    Query,
    extensions=[
        ApolloTracingExtension,
    ],
)
```

<Note>

If you are not running in an Async context then you'll need to use the sync
version:

```python
import strawberry
from strawberry.extensions.tracing import ApolloTracingExtensionSync


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


schema = strawberry.Schema(
    Query,
    extensions=[
        ApolloTracingExtensionSync,
    ],
)
```

</Note>

## API reference:

_No arguments_
