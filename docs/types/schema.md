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

---

### `.execute()` (async)

Executes a GraphQL operation against a schema (async)

`execute(query, variable_values, context_value, root_value, operation_name, validate_queries)`

| Parameter name   | Type                                   | Default | Description                                                                                            |
| ---------------- | -------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| query            | `str`                                  | N/A     | The document to be executed                                                                            |
| variable_values  | `Optional[Dict[str, Any]]`             | `None`  | The variables for this operation                                                                       |
| context_value    | `Optional[Any]`                        | `None`  | The value of the context that will be passed down to resolvers                                         |
| root_value       | `Optional[Any]`                        | `None`  | The value for the root type that will passed down to root resolvers                                    |
| operation_name   | `Optional[str]`                        | `None`  | The name of the operation you want to execute, useful when sending a document with multiple operations |
| validate_queries | `bool`                                 | `True`  | This flag enables/disables query validation                                                            |
| validation_rules | `Optional[List[Type[ValidationRule]]]` | `None`  | List of GraphQL core validation rules                                                                  |

---

### `.execute_sync()`

Executes a GraphQL operation against a schema

`execute_sync(query, variable_values, context_value, root_value, operation_name, validate_queries)`

| Parameter name   | Type                                   | Default | Description                                                                                            |
| ---------------- | -------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| query            | `str`                                  | N/A     | The document to be executed                                                                            |
| variable_values  | `Optional[Dict[str, Any]]`             | `None`  | The variables for this operation                                                                       |
| context_value    | `Optional[Any]`                        | `None`  | The value of the context that will be passed down to resolvers                                         |
| root_value       | `Optional[Any]`                        | `None`  | The value for the root type that will passed down to root resolvers                                    |
| operation_name   | `Optional[str]`                        | `None`  | The name of the operation you want to execute, useful when sending a document with multiple operations |
| validate_queries | `bool`                                 | `True`  | This flag allows to disable query validation                                                           |
| validation_rules | `Optional[List[Type[ValidationRule]]]` | `None`  | List of GraphQL core validation rules                                                                  |

## Query validation

When creating a schema you can decide to disable the validation of the queries
sent from clients. This can be useful to improve performances in some specific
cases, for example when dealing with internal APIs where queries can be trusted.

> ⚠️ NOTE: make sure you understand the trade-offs of disabling validation, for
> example when asking for field that don't exist the GraphQL schema won't return
> any error, which is something that breaks the safety of having a typed schema.

## Handling execution errors

By default Strawberry will log any errors encountered during a query execution to a `strawberry.execution` logger. This behaviour can be changed by overriding the `process_errors` function on the `strawberry.Schema` class.

The default functionality looks like this:

```python
# strawberry/schema/schema.py
from strawberry.types import ExecutionContext

logger = logging.getLogger("strawberry.execution")

class Schema:
    ...

    def process_errors(self, errors: List[GraphQLError], execution_context: ExecutionContext) -> None:
        for error in errors:
            # A GraphQLError wraps the underlying error so we have to access it
            # through the `original_error` property
            # https://graphql-core-3.readthedocs.io/en/latest/modules/error.html#graphql.error.GraphQLError
            actual_error = error.original_error or error
            logger.error(actual_error, exc_info=actual_error)
```
