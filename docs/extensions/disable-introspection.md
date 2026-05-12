---
title: Disable Introspection
summary: Disable standard GraphQL introspection queries.
tags: security,validation
---

# `DisableIntrospection`

The `DisableIntrospection` extension disables standard GraphQL introspection
queries for the schema. It blocks fields such as `__schema` and `__type`.

This can be useful to prevent clients from discovering unreleased or internal
features of the API through GraphQL introspection.

<Warning>

`DisableIntrospection` does not block non-introspection fields that may expose
schema information. For example, Apollo Federation schemas expose `_service`
and its `sdl` field so gateways and routers can compose federated services. If
you use `strawberry.federation.Schema`, protect federated endpoints from
untrusted clients with your own authentication, authorization, or network
controls.

</Warning>

## Usage example:

```python
import strawberry
from strawberry.extensions import DisableIntrospection


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


schema = strawberry.Schema(
    Query,
    extensions=[
        DisableIntrospection(),
    ],
)
```

## API reference:

_No arguments_

## Example query:

Running any query including the introspection field `__schema` will result in
an error. Consider the following query, for example:

```graphql
query {
  __schema {
    __typename
  }
}
```

Running it against the schema with the `DisableIntrospection` extension enabled
will result in an error response indicating that introspection has been
disabled:

```json
{
  "data": null,
  "errors": [
    {
      "message": "GraphQL introspection has been disabled, but the requested query contained the field '__schema'.",
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ]
    }
  ]
}
```
