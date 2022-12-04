---
title: Invalid Type for Union Error
---

# Invalid Type for Union Error

## Description

This error is thrown when trying to create an union with one or more type that's
are allowed in unions, for example the following code will throw this error:

```python
import strawberry


@strawberry.type
class Example:
    name: str


ExampleUnion = strawberry.union("ExampleUnion", types=(Example, int))


@strawberry.type
class Query:
    field: ExampleUnion


schema = strawberry.Schema(query=Query)
```

This happens because GraphQL doesn't support scalars as union members.

## How to fix this error

Since GraphQL doesn't allow scalars as union members, a workaround is to create
a wrapper type that contains the scalar value and use that instead. For example
the following code will create a union type between `Example` and `IntWrapper`
which is a wrapper on top of the `int` scalar:

```python
import strawberry


@strawberry.type
class Example:
    name: str


@strawberry.type
class IntWrapper:
    value: int


ExampleUnion = strawberry.union("ExampleUnion", types=(Example, IntWrapper))


@strawberry.type
class Query:
    field: ExampleUnion


schema = strawberry.Schema(query=Query)
```
