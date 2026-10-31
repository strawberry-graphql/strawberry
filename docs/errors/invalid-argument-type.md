---
title: Invalid Argument Type Error
---

# Invalid Argument Type Error

## Description

This error is thrown when an argument is of the wrong type, it usually happens
when passing **unions** or **interfaces** as an argument, or when marking an
argument with `strawberry.Private`, for example the following code will throw
this error:

```python
import strawberry

from typing import Union, Annotated


@strawberry.type
class TypeA:
    id: strawberry.ID


ExampleUnion = Annotated[Union[TypeA], strawberry.union("ExampleUnion")]


@strawberry.type
class Query:
    @strawberry.field
    def example(self, data: ExampleUnion) -> str:
        return "this is an example"


schema = strawberry.Schema(query=Query)
```

## Using union types as arguments

The latest [GraphQL specification](https://spec.graphql.org/October2021/)
doesn't allow using unions as arguments. If clients need to pass one of several
types, you can use a
[one of input type](../types/input-types.md#one-of-input-types) instead, with a
field for each type, of which clients set exactly one:

```python
import strawberry


@strawberry.input
class TypeAInput:
    id: strawberry.ID


@strawberry.input
class TypeBInput:
    name: str


@strawberry.input(one_of=True)
class ExampleInput:
    a: TypeAInput | None
    b: TypeBInput | None


@strawberry.type
class Query:
    @strawberry.field
    def example(self, data: ExampleInput) -> str:
        return "this is an example"
```

## Using `strawberry.Private` on arguments

[`strawberry.Private`](../types/private.md) only hides fields. Every resolver
parameter, except `self`, `root`, `info` and `strawberry.Parent`, is exposed as
an argument, so it can't be private:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def users(self, limit: strawberry.Private[int]) -> list[str]:
        return []
```

Remove `strawberry.Private` to expose the argument in the schema, or pass the
value to the resolver another way, for example through the
[context](../types/resolvers.md#accessing-execution-information).
