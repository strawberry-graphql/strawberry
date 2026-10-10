---
title: Inherited Default Factory Error
---

# Inherited Default Factory Error

## Description

This error is thrown when a `strawberry.pydantic.input` inherits a field with a
default factory from a Strawberry input type, for example the following code
will throw this error:

```python
import pydantic
import strawberry


@strawberry.input
class Pagination:
    tags: list[str] | None = strawberry.field(default_factory=list)


@strawberry.pydantic.input
class SearchInput(pydantic.BaseModel, Pagination):
    query: str
```

This happens because Strawberry types are dataclasses, which don't keep a
field's default factory on the class. Pydantic doesn't see the factory, so the
field would be required by Pydantic and the factory would never be used.

## How to fix this error

You can fix this error by declaring the field with its default factory on the
Pydantic model:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class SearchInput(pydantic.BaseModel):
    query: str
    tags: list[str] | None = pydantic.Field(default_factory=list)
```
