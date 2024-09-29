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
class Schema(Query, mutation=None, subscription=None, **kwargs): ...
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

Pass a `StrawberryConfig` object to configure how the schema is generated.
[Read more](/docs/types/schema-configurations).

#### `types: List[Type] = []`

List of extra types to register with the Schema that are not directly linked to
from the root Query.

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
    def get_customer(
        self, id: strawberry.ID
    ) -> Customer:  # note we're returning the interface here
        if id == "mark":
            return Individual(name="Mark", date_of_birth=date(1984, 5, 14))

        if id == "facebook":
            return Company(name="Facebook", founded=date(2004, 2, 1))


schema = strawberry.Schema(Query, types=[Individual, Company])
```

</details>

#### `extensions: List[Type[SchemaExtension]] = []`

List of [extensions](/docs/extensions) to add to your Schema.

#### `scalar_overrides: Optional[Dict[object, ScalarWrapper]] = None`

Override the implementation of the built in scalars.
[More information](/docs/types/scalars#overriding-built-in-scalars).

---

## Methods

### `.execute()` (async)

Executes a GraphQL operation against a schema (async)

```python
async def execute(
    query, variable_values, context_value, root_value, operation_name
): ...
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

The name of the operation you want to execute, useful when sending a document
with multiple operations. If no `operation_name` is specified the first
operation in the document will be executed.

### `.execute_sync()`

Executes a GraphQL operation against a schema

```python
def execute_sync(query, variable_values, context_value, root_value, operation_name): ...
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

The name of the operation you want to execute, useful when sending a document
with multiple operations. If no `operation_name` is specified the first
operation in the document will be executed.

---

## Handling execution errors

By default Strawberry will log any errors encountered during a query execution
to a `strawberry.execution` logger. This behaviour can be changed by overriding
the `process_errors` function on the `strawberry.Schema` class.

The default functionality looks like this:

```python
# strawberry/schema/base.py
from strawberry.types import ExecutionContext

logger = logging.getLogger("strawberry.execution")


class BaseSchema:
    ...

    def process_errors(
        self,
        errors: List[GraphQLError],
        execution_context: Optional[ExecutionContext] = None,
    ) -> None:
        for error in errors:
            StrawberryLogger.error(error, execution_context)
```

```python
# strawberry/utils/logging.py
from strawberry.types import ExecutionContext


class StrawberryLogger:
    logger: Final[logging.Logger] = logging.getLogger("strawberry.execution")

    @classmethod
    def error(
        cls,
        error: GraphQLError,
        execution_context: Optional[ExecutionContext] = None,
        # https://www.python.org/dev/peps/pep-0484/#arbitrary-argument-lists-and-default-argument-values
        **logger_kwargs: Any,
    ) -> None:
        # "stack_info" is a boolean; check for None explicitly
        if logger_kwargs.get("stack_info") is None:
            logger_kwargs["stack_info"] = True

        logger_kwargs["stacklevel"] = 3

        cls.logger.error(error, exc_info=error.original_error, **logger_kwargs)
```

## Filtering/customising fields

You can customise the fields that are exposed on a schema by subclassing the
`Schema` class and overriding the `get_fields` method, for example you can use
this to create different GraphQL APIs, such as a public and an internal API.
Here's an example of this:

```python
@strawberry.type
class User:
    name: str
    email: str = strawberry.field(metadata={"tags": ["internal"]})


@strawberry.type
class Query:
    user: User


def public_field_filter(field: StrawberryField) -> bool:
    return "internal" not in field.metadata.get("tags", [])


class PublicSchema(strawberry.Schema):
    def get_fields(
        self, type_definition: StrawberryObjectDefinition
    ) -> List[StrawberryField]:
        return list(filter(public_field_filter, type_definition.fields))


schema = PublicSchema(query=Query)
```

<Note>

The `get_fields` method is only called once when creating the schema, this is
not intended to be used to dynamically customise the schema.

</Note>

## Deprecating fields

Fields can be deprecated using the argument `deprecation_reason`.

<Note>

This does not prevent the field from being used, it's only for documentation.
See:
[GraphQL field deprecation](https://spec.graphql.org/June2018/#sec-Field-Deprecation).

</Note>

<CodeGrid>

```python
import strawberry
import datetime
from typing import Optional


@strawberry.type
class User:
    name: str
    dob: datetime.date
    age: Optional[int] = strawberry.field(deprecation_reason="Age is deprecated")
```

```graphql
type User {
  name: String!
  dob: Date!
  age: Int @deprecated(reason: "Age is deprecated")
}
```

</CodeGrid>
