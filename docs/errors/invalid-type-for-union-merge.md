---
title: Invalid Type for Union Merge Error
---

# Invalid Type for Union Merge Error

## Description

This error is thrown when trying to extend an union with a type that's not
allowed in unions, for example the following code will throw this error:

```python
import strawberry

from typing import Union, Annotated


@strawberry.type
class Example:
    name: str


ExampleUnion = Annotated[Union[Example], strawberry.union("ExampleUnion")]


@strawberry.type
class Query:
    field: ExampleUnion | int


schema = strawberry.Schema(query=Query)
```

This happens because GraphQL doesn't support scalars as union members.

## How to fix this error

At the moment Strawberry doesn't have a proper way to merge unions and types,
but you can still create a union type that combines multiple types manually.
Since GraphQL doesn't allow scalars as union members, a workaround is to create
a wrapper type that contains the scalar value and use that instead. For example
the following code will create a union type between `Example` and `IntWrapper`
which is a wrapper on top of the `int` scalar:

```python
import strawberry

from typing import Union, Annotated


@strawberry.type
class Example:
    name: str


@strawberry.type
class IntWrapper:
    value: int


ExampleUnion = Annotated[Union[Example, IntWrapper], strawberry.union("ExampleUnion")]


@strawberry.type
class Query:
    field: ExampleUnion


schema = strawberry.Schema(query=Query)
```
