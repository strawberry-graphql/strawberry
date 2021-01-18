---
title: Queries
---

# Queries

In GraphQL you use queries to fetch data from a server. In Strawberry you can
define the data your server provides by defining query types.

By default all the fields the API exposes are nested under a root Query type.

This is how you define a root query type in Strawberry:

```python
@strawberry.type
class Query:
    name: str

schema = strawberry.Schema(query=Query)
```

This creates a schema where the root type Query has one single field called
name.

As you notice we don't provide a way to fetch data. In order to do so we need to
provide a `resolver`, a function that knows how to fetch data for a specific
field.

For example in this case we could have a function that always returns the same
name:

```python
def get_name() -> str:
    return "Strawberry"

@strawberry.type
class Query:
    name: str = strawberry.field(resolver=get_name)

schema = strawberry.Schema(query=Query)
```

So now, when requesting the name field, the `get_name` function will be called.
