---
title: Resolver Field On Input Error
---

# Resolver Field On Input Error

## Description

This error is thrown when a `strawberry.pydantic.input` has a field with a
resolver, for example the following code will throw this error:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class CreateUserInput(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field
    def upper_name(self) -> str:
        return self.name.upper()
```

This happens because input types only hold the values sent by the client, so
their fields can't be resolved.

## How to fix this error

You can fix this error by removing the resolver, or by moving the field to an
output type:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class CreateUserInput(pydantic.BaseModel):
    name: str


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field
    def upper_name(self) -> str:
        return self.name.upper()
```

Resolver fields inherited from a base class shared with an output type are
ignored by inputs, so they don't raise this error.
