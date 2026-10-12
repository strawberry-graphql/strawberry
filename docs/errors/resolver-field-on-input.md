---
title: Resolver Field On Input Error
---

# Resolver Field On Input Error

## Description

This error is thrown when a field of an input type has a resolver, for example
the following code will throw this error:

```python
import strawberry


@strawberry.input
class UserInput:
    name: str

    @strawberry.field
    def upper_name(self) -> str:
        return self.name.upper()
```

This happens because input types only hold the values sent by the client, so
their fields can't be resolved: the resolver would never run, and every request
using the input would fail, as the field can't be passed to the input type.

The same applies to fields inherited from an output type, like in
`class UserInput(User)`, when `User` has fields with resolvers.

## How to fix this error

You can fix this error by removing the resolver, or by moving the field to an
output type:

```python
import strawberry


@strawberry.input
class UserInput:
    name: str


@strawberry.type
class User:
    name: str

    @strawberry.field
    def upper_name(self) -> str:
        return self.name.upper()
```

When the field is inherited, move the fields to share to a base type without
resolvers, and inherit from it in both types:

```python
import strawberry


@strawberry.type
class UserBase:
    name: str


@strawberry.type
class User(UserBase):
    @strawberry.field
    def upper_name(self) -> str:
        return self.name.upper()


@strawberry.input
class UserInput(UserBase):
    pass
```

## Pydantic inputs

`strawberry.pydantic.input` raises this error too, for fields with a resolver
defined on the input model:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class UserInput(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field
    def upper_name(self) -> str:
        return self.name.upper()
```

Fields with a resolver inherited from a base model, for example one shared with
an output type, are ignored by Pydantic inputs, so they don't raise this error:

```python
import pydantic
import strawberry


class UserBase(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field
    def upper_name(self) -> str:
        return self.name.upper()


@strawberry.pydantic.type
class User(UserBase):
    pass


@strawberry.pydantic.input
class UserInput(UserBase):
    pass
```
