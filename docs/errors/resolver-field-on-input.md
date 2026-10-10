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
