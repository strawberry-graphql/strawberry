---
title: Unsupported Field Override Error
---

# Unsupported Field Override Error

## Description

This error is thrown when a `strawberry.pydantic` type overrides a field with a
resolver, inherited from a base model or an interface, with something that isn't
a field, like a method without `@strawberry.pydantic.field`. For example the
following code will throw this error:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field
    def greeting(self) -> str:
        return f"Hi {self.name}"


@strawberry.pydantic.type
class Admin(User):
    def greeting(self) -> str:
        return f"Welcome back, {self.name}"
```

This happens because the method replaces the inherited one, so `Admin` wouldn't
have a `greeting` field anymore, even though it most likely should.

The same error is thrown when a field with a resolver has the name of a field
of the model, as Pydantic would use the method as the default value of the
field, and never call the resolver.

Fields of the model and computed fields can still override inherited fields with
a resolver, unless computed fields are left out with `include_computed=False`.

## How to fix this error

To change the resolver of an inherited field, decorate the method with
`@strawberry.pydantic.field`:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field
    def greeting(self) -> str:
        return f"Hi {self.name}"


@strawberry.pydantic.type
class Admin(User):
    @strawberry.pydantic.field
    def greeting(self) -> str:
        return f"Welcome back, {self.name}"
```

If the method isn't meant to be part of the GraphQL type, rename it, so that the
inherited field is kept. A resolver with the name of a field of the model needs
another name, unless the model field is removed.

To have a field with a resolver only on some of the types that share a base
model, move it to a base model that only those types extend:

```python
import pydantic
import strawberry


class UserBase(pydantic.BaseModel):
    name: str


class GreeterBase(UserBase):
    @strawberry.pydantic.field
    def greeting(self) -> str:
        return f"Hi {self.name}"


@strawberry.pydantic.type
class User(GreeterBase):
    pass


@strawberry.pydantic.type
class Admin(UserBase):
    pass
```
