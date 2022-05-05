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

```python
class Schema(Query, mutation=None, subscription=None, **kwargs)
```

<!-- TODO: add docs on directives, types, extensions and execution context class -->

#### `query: Type`

The root query Strawberry type. Usually called `Query`.

<Note>

A query type is always required when creating a Schema.

</Note>

#### `mutation: Optional[Type] = None`

The root mutation type. Usually called `Mutation`.

#### `subscription: Optional[Type] = None`

The root subscription type. Usually called `Subscription`.

#### `config: Optional[StrawberryConfig] = None`

Pass a `StrawberryConfig` object to configure how the schema is generated. [Read
more](/docs/types/schema-configurations).

#### `types: List[Type] = []`

List of extra types to register with the Schema that are not directly linked
to from the root Query.

<details class="mb-4">
<summary>Defining extra `types` when using Interfaces</summary>

```python
from datetime import date
import strawberry

@strawberry.interface
class Customer:
    name: str

@strawberry.type
class Individual(Customer):
    date_of_birth: date

@strawberry.type
class Company(Customer):
    founded: date

@strawberry.type
class Query:
    @strawberry.field
    def get_customer(self, id: strawberry.ID) -> Customer  # note we're returning the interface here
        if id == "mark":
            return Individual(name="Mark", date_of_birth=date(1984, 5, 14))

        if id == "facebook":
            return Company(name="Facebook", founded=date(2004, 2, 1))

schema = strawberry.Schema(Query, types=[Individual, Company])
```

</details>

#### `extensions: List[Type[Extension]] = []`

List of [extensions](/docs/extensions) to add to your Schema.

#### `scalar_overrides: Optional[Dict[object, ScalarWrapper]] = None`

Override the implementation of the built in scalars. [More information](/docs/types/scalars#overriding-built-in-scalars).

---

## Methods

### `.execute()` (async)

Executes a GraphQL operation against a schema (async)

```python
async def execute(query, variable_values, context_value, root_value, operation_name)
```

#### `query: str`

The GraphQL document to be executed.

#### `variable_values: Optional[Dict[str, Any]] = None`

The variables for this operation.

#### `context_value: Optional[Any] = None`

The value of the context that will be passed down to resolvers.

#### `root_value: Optional[Any] = None`

The value for the root value that will passed to root resolvers.

#### `operation_name: Optional[str] = None`

The name of the operation you want to execute, useful when sending a document with multiple operations. If no `operation_name` is specified the first operation in the document will be executed.

### `.execute_sync()`

Executes a GraphQL operation against a schema

```python
def execute_sync(query, variable_values, context_value, root_value, operation_name)`
```

#### `query: str`

The GraphQL document to be executed.

#### `variable_values: Optional[Dict[str, Any]] = None`

The variables for this operation.

#### `context_value: Optional[Any] = None`

The value of the context that will be passed down to resolvers.

#### `root_value: Optional[Any] = None`

The value for the root value that will passed to root resolvers.

#### `operation_name: Optional[str] = None`

The name of the operation you want to execute, useful when sending a document with multiple operations. If no `operation_name` is specified the first operation in the document will be executed.

---

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
