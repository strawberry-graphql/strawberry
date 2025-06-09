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
