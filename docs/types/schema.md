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

## API reference

<!-- TODO: add docs on directives, types, extensions and execution context class -->

**`query: Type`**

The root query Strawberry type. Usually called `Query`.

*Note:* a query type is always required when creating a Schema.

**`mutation: Optional[Type] = None`**

The root mutation type. Usually called `Mutation`.

**`subscription: Optional[Type] = None`**

The root subscription type. Usually called `Subscription`.

**`config: Optional[StrawberryConfig] = None`**

...

TODO: example

**`directives`**

*TODO*

TODO: example

**`types: List[Type] = []`**

List of extra types to register with the Schema that are not directly linked
to from the root Query. This is often used if you're using Interfaces ...

TODO: example

**`extensions: List[Type[Extension]] = []`**

...

TODO: example

**`scalar_overrides: ...`**

...

TODO: example

---

### `.execute()` (async)

Executes a GraphQL operation against a schema (async)

`execute(query, variable_values, context_value, root_value, operation_name)`

| Parameter name   | Type                                   | Default | Description                                                                                            |
| ---------------- | -------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| query            | `str`                                  | N/A     | The document to be executed                                                                            |
| variable_values  | `Optional[Dict[str, Any]]`             | `None`  | The variables for this operation                                                                       |
| context_value    | `Optional[Any]`                        | `None`  | The value of the context that will be passed down to resolvers                                         |
| root_value       | `Optional[Any]`                        | `None`  | The value for the root type that will passed down to root resolvers                                    |
| operation_name   | `Optional[str]`                        | `None`  | The name of the operation you want to execute, useful when sending a document with multiple operations |

---

### `.execute_sync()`

Executes a GraphQL operation against a schema

`execute_sync(query, variable_values, context_value, root_value, operation_name)`

| Parameter name   | Type                                   | Default | Description                                                                                            |
| ---------------- | -------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| query            | `str`                                  | N/A     | The document to be executed                                                                            |
| variable_values  | `Optional[Dict[str, Any]]`             | `None`  | The variables for this operation                                                                       |
| context_value    | `Optional[Any]`                        | `None`  | The value of the context that will be passed down to resolvers                                         |
| root_value       | `Optional[Any]`                        | `None`  | The value for the root type that will passed down to root resolvers                                    |
| operation_name   | `Optional[str]`                        | `None`  | The name of the operation you want to execute, useful when sending a document with multiple operations |

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
