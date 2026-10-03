---
title: Not A Pydantic Model Error
---

# Not A Pydantic Model Error

## Description

This error is thrown when a `strawberry.pydantic` decorator is used on a class
that isn't a Pydantic v2 model, for example the following code will throw this
error:

```python
import strawberry


@strawberry.pydantic.type
class User:
    name: str
```

This happens because the `strawberry.pydantic` decorators read the fields from
the model's Pydantic definition. Pydantic dataclasses and Pydantic v1 models
(`pydantic.v1.BaseModel`) aren't supported either.

## How to fix this error

You can fix this error by using `strawberry.type` (or `strawberry.input` and
`strawberry.interface`) for classes that aren't Pydantic models:

```python
import strawberry


@strawberry.type
class User:
    name: str
```

Or by making the class a Pydantic v2 model:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
```

For Pydantic v1 models, use `strawberry.experimental.pydantic`.
