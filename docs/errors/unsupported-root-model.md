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

And so will this code:

```python
import pydantic
import strawberry


class Tags(pydantic.RootModel[list[str]]):
    pass


@strawberry.pydantic.input
class CreatePostInput(pydantic.BaseModel):
    title: str
    tags: Tags
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
