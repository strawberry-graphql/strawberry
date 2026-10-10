---
title: Unregistered Pydantic Type Error
---

# Unregistered Pydantic Type Error

## Description

This error is thrown when a field of a `strawberry.pydantic` type uses a
Pydantic model that isn't a Strawberry type, for example the following code will
throw this error:

```python
import pydantic
import strawberry


class Address(pydantic.BaseModel):
    street: str


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    address: Address
```

This happens because Strawberry needs to know the GraphQL type of every field,
and `Address` hasn't been converted to a GraphQL type.

## How to fix this error

You can fix this error by decorating the model used by the field, with
`@strawberry.pydantic.type` for output types and `@strawberry.pydantic.input`
for inputs:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class Address(pydantic.BaseModel):
    street: str


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    address: Address
```
