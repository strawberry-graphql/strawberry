---
title: Unsupported Root Model Error
---

# Unsupported Root Model Error

## Description

This error is thrown when a Pydantic `RootModel` is decorated with
`@strawberry.pydantic.type`, `@strawberry.pydantic.input` or
`@strawberry.pydantic.interface`, or when a field of a `strawberry.pydantic`
type uses one, for example the following code will throw this error:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class Tags(pydantic.RootModel[list[str]]):
    pass
```

An unregistered `RootModel` field also raises the error when the schema is
built:

```python
import pydantic
import strawberry


class Tags(pydantic.RootModel[list[str]]):
    pass


@strawberry.pydantic.input
class CreatePostInput(pydantic.BaseModel):
    title: str
    tags: Tags


@strawberry.type
class Query:
    ok: bool


schema = strawberry.Schema(query=Query, types=[CreatePostInput])
```

This happens because a `RootModel` holds a single value instead of fields, so it
can't be a GraphQL object type or input.

A `RootModel` field can instead be exposed through an `Annotated` custom scalar,
or registered as a scalar in the schema's `scalar_map` to keep existing model
annotations unchanged.

## How to fix this error

You can fix this error by using the type of the root value instead of the
`RootModel`:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class CreatePostInput(pydantic.BaseModel):
    title: str
    tags: list[str]
```
