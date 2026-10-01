---
title: Unsupported Root Model Error
---

# Unsupported Root Model Error

## Description

This error is thrown when a Pydantic `RootModel` is decorated with
`@strawberry.pydantic.type`, `@strawberry.pydantic.input` or
`@strawberry.pydantic.interface`, for example the following code will throw this
error:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class Tags(pydantic.RootModel[list[str]]):
    pass
```

This happens because a `RootModel` holds a single value instead of fields, so it
can't be a GraphQL object type or input.

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
