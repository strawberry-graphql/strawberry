---
title: Disable Introspection
summary: Disable all introspection queries.
tags: security,validation
---

# `DisableIntrospection`

The `DisableIntrospection` extension disables all introspection queries for the
schema. This can be useful to prevent clients from discovering unreleased or
internal features of the API.

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

Running any query including the introspection field `__schema` will result in an
error. Consider the following query, for example:

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
