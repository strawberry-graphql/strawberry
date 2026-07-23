---
title: TypedDicts
---

# TypedDicts

While Strawberry typically uses Python classes to define GraphQL types, you
might prefer working with standard Python dictionaries, especially when
integrating with external APIs, databases, or legacy codebases that already
return dictionaries.

Strawberry provides native support for converting Python's `typing.TypedDict`
definitions into GraphQL Object Types and Input Types. To use this, decorate a
`TypedDict` with `@strawberry.type` or `@strawberry.input` to expose it in your
schema while continuing to work with standard Python dictionaries at runtime.

Also note that a `TypedDict` used in nested positions should not be shared
between input and output definitions. If the same structure is needed in both
positions, define separate TypedDict classes for the input and output
representations.

## Output Types

To define a GraphQL Object Type that resolves from a dictionary, decorate a
`TypedDict` with `@strawberry.type`.

<CodeGrid>

```python
import strawberry
from typing import TypedDict


@strawberry.type
class UserDict(TypedDict):
    id: int
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def get_user(self) -> UserDict:
        # We can return a standard dictionary directly!
        return {"id": 1, "name": "Alice"}
```

```graphql
type UserDict {
  id: Int!
  name: String!
}

type Query {
  getUser: UserDict!
}
```

</CodeGrid>

## Input Types

Similarly, you can define GraphQL Input Types by decorating a `TypedDict` with
`@strawberry.input`. This allows your mutation resolvers to receive standard
dictionaries instead of instantiated objects.

<CodeGrid>

```python
import strawberry
from typing import TypedDict


@strawberry.input
class CreateUserInput(TypedDict):
    name: str
    age: int


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, data: CreateUserInput) -> bool:
        # data is a dictionary: {"name": "Bob", "age": 30}
        print(f"Creating user: {data['name']}")
        return True
```

```graphql
input CreateUserInput {
  name: String!
  age: Int!
}

type Mutation {
  createUser(data: CreateUserInput!): Boolean!
}
```

</CodeGrid>

## Nullability and Required Keys

GraphQL nullability, whether a field has a `!`, is determined by whether a key
is explicitly required to exist in the dictionary. Strawberry fully supports
Python's advanced TypedDict nullability rules, including `total=False`,
`Required`, and `NotRequired`.

### `total=False`

By default, all keys in a `TypedDict` are required. If you set `total=False`,
all keys become optional and therefore nullable in GraphQL.

<CodeGrid>

```python
import strawberry
from typing import TypedDict


@strawberry.type
class PartialUser(TypedDict, total=False):
    name: str
    email: str
```

```graphql
type PartialUser {
  name: String
  email: String
}
```

</CodeGrid>

### Mixing `Required` and `NotRequired`

You can fine-tune exactly which keys are required using `Required` and
`NotRequired` (available in `typing` in Python 3.11+, or `typing_extensions` in
older versions).

<CodeGrid>

```python
import sys

import strawberry

# For Python < 3.11, use typing_extensions.
if sys.version_info >= (3, 11):
    from typing import NotRequired, Required, TypedDict
else:
    from typing import TypedDict

    from typing_extensions import NotRequired, Required


@strawberry.type
class UpdateUserDict(TypedDict, total=False):
    # 'id' MUST be provided, even though total=False
    id: Required[int]

    # 'name' is optional
    name: NotRequired[str]
```

```graphql
type UpdateUserDict {
  id: Int!
  name: String
}
```

</CodeGrid>

<Note>

`Optional[str]` means the key must exist in the dictionary, but its value can be
`None`. `NotRequired[str]` means the key can be completely missing from the
dictionary. Strawberry respects this distinction internally, though both compile
to a nullable `String` in the final GraphQL schema.

</Note>

## Metadata and Directives

Because `TypedDict` does not support Strawberry's standard `strawberry.field()`
assignment, for example `name: str = strawberry.field(...)`, you must use
`typing.Annotated` to attach GraphQL descriptions and directives to the fields.

<CodeGrid>

```python
import strawberry
from typing import Annotated, TypedDict


@strawberry.type
class BookDict(TypedDict):
    # You can pass a string directly for a description...
    id: Annotated[int, "The unique ISBN of the book"]

    # ...or use strawberry.field() to attach directives
    title: Annotated[
        str,
        strawberry.field(description="The book title"),
    ]
```

```graphql
type BookDict {
  """
  The unique ISBN of the book
  """
  id: Int!

  """
  The book title
  """
  title: String!
}
```

</CodeGrid>

## Runtime Validation

When returning a standard Strawberry Object Type, missing fields will often
trigger immediate errors during instantiation. However, because dictionaries are
evaluated lazily during GraphQL execution, a missing required key will result in
a cryptic `KeyError` late in the request lifecycle.

To prevent this, Strawberry provides a `validate_typed_dict` utility. You can
use it inside your resolvers to guarantee the dictionary matches the GraphQL
contract before returning it.

```python
from typing import TypedDict

import strawberry

from strawberry.types.typed_dict import TypedDictValidationError, validate_typed_dict


@strawberry.type
class Point2D(TypedDict):
    x: int
    y: int


@strawberry.type
class Query:
    @strawberry.field
    def get_point(self) -> Point2D:
        data = {"x": 10}  # No y

        # This will raise a TypedDictValidationError
        validate_typed_dict(data, Point2D)

        return data
```

## TypedDicts in Unions

TypedDict-based GraphQL types can be used as members of Strawberry unions.

When a resolver returns a plain dictionary, Strawberry uses the TypedDict's
required keys to determine whether the value matches a union member.

If multiple union members match the same dictionary shape, the selected type
depends on union resolution order. For unambiguous results, ensure union members
can be distinguished by their required fields.

```python
@strawberry.type
class BasicUserDict(TypedDict):
    id: int


@strawberry.type
class AdminUserDict(TypedDict):
    id: int
    permissions: list[str]


UserAccountUnion = Annotated[
    BasicUserDict | AdminUserDict,
    strawberry.union("UserAccount"),
]
```

### Union Resolution Caveats

Because TypedDict union resolution is based on required keys rather than runtime
type identity, ambiguity can occur when one TypedDict's required keys are a
subset of another's.

For example, this dictionary:

```python
{
    "id": 1,
    "permissions": ["*"],
}
```

matches both of the aforementioned TypedDict examples:

```python
class BasicUserDict(TypedDict):
    id: int


class AdminUserDict(TypedDict):
    id: int
    permissions: list[str]
```

It matches `AdminUserDict` because it has `id` and `permissions`, but it also
matches `BasicUserDict` because it satisfies the requirement of having an `id`.

In this scenario, Strawberry cannot intrinsically know which type you intended,
and will resolve to the first match it evaluates.

For predictable union resolution, prefer union members whose required keys do
not overlap ambiguously, or return values with explicit runtime type
information.

## API Reference

### `@strawberry.type`

Can be applied directly to a TypedDict to create a GraphQL object type.

- `name` (`str`): Override the GraphQL name. Defaults to the CamelCase class
  name.
- `description` (`str`): Set a GraphQL description for the type.
- `directives` (`Iterable[object]`): A list of GraphQL directives to apply to
  the type.

### `@strawberry.input`

Can be applied directly to a TypedDict to create a GraphQL input type.

- `name` (`str`): Override the GraphQL name. Defaults to the CamelCase class
  name.
- `description` (`str`): Set a GraphQL description for the type.
- `directives` (`Iterable[object]`): A list of GraphQL directives to apply to
  the type.

### `validate_typed_dict`

- `validate_typed_dict(data: dict, typed_dict_cls: Type)`: Evaluates the
  provided dictionary against the requirements of the given Strawberry-decorated
  `TypedDict` and raises a `TypedDictValidationError` if any required keys are
  missing.
