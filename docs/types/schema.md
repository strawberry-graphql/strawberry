---
title: Schema
---

# Schema

Every GraphQL API has a schema and that is used to define all the
functionalities for an API. A schema is defined by passing 3
[object types](./object-types): `Query`, `Mutation` and `Subscription`.

`Mutation` and `Subscription` are optional, meanwhile `Query` has to always be
there.

This is an example of a schema defined using Strawberry:

```python
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello World"


schema = strawberry.Schema(Query)
```

## API

```python
strawberry.Schema(
    query: Type,
    mutation: Type = None,
    subscription: Type = None
    validate_queries: bool = True
)
```

<!-- TODO: add docs on directives, types, extensions and execution context class -->

Creates a GraphQL schema

- `query`: The root query type
- `mutation`: The root mutation type
- `subscription`: The root subscription type
- `validate_queries`: This flag allows to disable query validation (see below)

## Query validation

When creating a schema you can decide to opt-out from validating the queries
sent from clients. This can be useful to improve performances in some specific
cases, for example when dealing with internal APIs where queries can be trusted.

> ⚠️ NOTE: make sure you understand the trade-offs of disabling validation, for
> example when asking for field that don't exist the GraphQL schema won't return
> any error, which is something that breaks the safety of having a typed schema.
