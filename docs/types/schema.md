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

```python
async Schema().execute(
    query: str,
    variable_values: Optional[Dict[str, Any]] = None,
    context_value: Optional[Any] = None,
    root_value: Optional[Any] = None,
    operation_name: Optional[str] = None,
    validate_queries: Optional[bool] = True,
) -> ExecutionResult:
```

Executes a GraphQL operation:

- `query`: The document to be executed
- `variable_values`: The variables for this operation
- `context_value`: The value of the context that will be passed down to
  resolvers
- `root_value`: The value for the root type that will passed down to root
  resolvers
- `operation_name`: The name of the operation you want to execute, useful when
  sending a document with multiple operations
- `validate_queries`: This flag allows to disable query validation

```python
Schema().execute_sync(
    query: str,
    variable_values: Optional[Dict[str, Any]] = None,
    context_value: Optional[Any] = None,
    root_value: Optional[Any] = None,
    operation_name: Optional[str] = None,
    validate_queries: Optional[bool] = True,
) -> ExecutionResult:
```

Sync version of `Schema().execute`

## Query validation

When creating a schema you can decide to opt-out from validating the queries
sent from clients. This can be useful to improve performances in some specific
cases, for example when dealing with internal APIs where queries can be trusted.

> ⚠️ NOTE: make sure you understand the trade-offs of disabling validation, for
> example when asking for field that don't exist the GraphQL schema won't return
> any error, which is something that breaks the safety of having a typed schema.
