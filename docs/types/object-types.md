---
title: Object types
---

# Object types

Object types are the fundamentals of any GraphQL schema, they are used to define
the kind of objects that exist in a schema. Object types are created by defining
a name and a list of fields, here’s an example object type defined using the
GraphQL schema language:

```graphql
type Character {
  name: String!
  age: Int!
}
```

## A note on Query, Mutation and Subscription

While reading about GraphQL you might have encountered 3 special object types:
`Query`, `Mutation` and `Subscription`. They are defined as standard object
types, with the difference that they are also used as entry points for your
schema (also referred as root types).

- `Query` is the entry point for all the query operations
- `Mutation` is the entry point for all the mutations
- `Subscription` is the entry point for all the subscriptions.

For a walk-through on how to define schemas, read the
[schema basics](../general/schema-basics.md).

## Defining object types

In Strawberry, you can define object types by using the `@strawberry.type`
decorator, like this:

<CodeGrid>

```python
import strawberry


@strawberry.type
class Character:
    name: str
    age: int
```

```graphql
type Character {
  name: String!
  age: int!
}
```

</CodeGrid>

You can also refer to other types, like this:

<CodeGrid>

```python
import strawberry


@strawberry.type
class Character:
    name: str
    age: int


@strawberry.type
class Book:
    title: str
    main_character: Character
```

```graphql
type Character {
  name: String!
  age: Int!
}

type Book {
  title: String!
  mainCharacter: Character!
}
```

</CodeGrid>

## Customizing fields with `Annotated`

You can configure fields by adding `strawberry.field()` to
[`typing.Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated).
This syntax works on object types, input types, and interfaces, including when
using `from __future__ import annotations`:

```python
from typing import Annotated

import strawberry


@strawberry.type
class User:
    name: Annotated[
        str,
        strawberry.field(name="displayName", description="The displayed name"),
    ]
    tags: Annotated[list[str], strawberry.field(default_factory=list)]
```

All `strawberry.field()` options are supported. In particular, `default` and
`default_factory` also configure the generated dataclass constructor, so
`User(name="Patrick")` in the example above gets a new empty `tags` list.

On Python 3.10 through 3.13, use `strawberry.lazy()` when the field type is only
imported under `TYPE_CHECKING` or otherwise unavailable at runtime. This form
works together with field metadata:

```python
from typing import TYPE_CHECKING, Annotated

import strawberry

if TYPE_CHECKING:
    from .users import User


@strawberry.type
class Post:
    author: Annotated[
        "User",
        strawberry.lazy(".users"),
        strawberry.field(description="The post author"),
    ]
```

Python 3.14 and newer can also preserve the field metadata on a direct
unresolved reference without `strawberry.lazy()`.

The field configuration can be combined with other Strawberry metadata. The
order of the metadata does not matter:

```python
@strawberry.type
class Query:
    result: Annotated[
        Success | Failure,
        strawberry.union("Result"),
        strawberry.field(description="The operation result"),
    ]
```

Use only one `strawberry.field()` for each field. You can alternatively use the
equivalent assignment syntax, such as
`name: str = strawberry.field(description="The displayed name")`.

`strawberry.field()` must be metadata on the field's outermost `Annotated` type.
Placing it inside a wrapper configures no GraphQL field, so Strawberry raises an
error instead of silently ignoring it:

```python
# Incorrect: strawberry.field() describes the list item, not `names`.
names: list[Annotated[str, strawberry.field(description="A name")]]

# Correct: strawberry.field() describes `names`.
names: Annotated[list[str], strawberry.field(description="The names")]
```

## Extending types

Sometimes a type is best assembled from more than one place — a plugin adding a
field to a type owned by the core of your application, or a large schema split
across modules that should not import each other.

Passing `extend=True` lets a second class contribute fields to an existing
GraphQL type instead of clashing with it. Both classes use the same GraphQL
name; the extension's fields are merged into the base type:

<CodeGrid>

```python
import strawberry


@strawberry.type(name="User")
class User:
    name: str


@strawberry.type(name="User", extend=True)
class UserAvatar:
    @strawberry.field
    def avatar_url(self) -> str:
        return f"https://example.com/avatar/{self.name}"


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Ada")


schema = strawberry.Schema(query=Query, types=[UserAvatar])
```

```graphql
type Query {
  user: User!
}

type User {
  name: String!
}

extend type User {
  avatarUrl: String!
}
```

</CodeGrid>

The extension must be reachable by the schema. If nothing in the schema refers
to it, pass it through the `types` argument as shown above.

Extensions may only add fields. Redefining a field that the base type — or
another extension — already declares raises a `TypeError`, so two modules cannot
silently disagree about what a field means:

```python
@strawberry.type(name="User")
class User:
    name: str


@strawberry.type(name="User", extend=True)
class UserConflict:
    name: str


# TypeError: Type User defines duplicate extension field(s): name
```

<Note>

`extend=True` is also how Apollo Federation marks a type that is owned by
another subgraph, which is why the printed SDL uses `extend type`. Merging only
happens when a base type with the same name exists in the same schema; a
federated type declared once behaves exactly as before.

</Note>

## API

`@strawberry.type(name: str = None, description: str = None, extend: bool = False)`

Creates an object type from a class definition.

`name`: if set this will be the GraphQL name, otherwise the GraphQL will be
generated by camel-casing the name of the class.

`description`: this is the GraphQL description that will be returned when
introspecting the schema or when navigating the schema using GraphiQL.

`extend`: marks the class as extending an existing GraphQL type. When another
type with the same GraphQL name is present, this class's fields are merged into
it and the type is printed as `extend type`.
