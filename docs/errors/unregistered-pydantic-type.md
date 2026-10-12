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

You can fix this error by decorating the model used by the field with
`@strawberry.pydantic.type`:

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

Subclasses of decorated models need their own decorator too, as they can have
fields of their own. Otherwise the field would silently use the base model's
GraphQL type, without the subclass's fields:

```python
@strawberry.pydantic.type
class Animal(pydantic.BaseModel):
    name: str


@strawberry.pydantic.type
class Dog(Animal):
    breed: str


@strawberry.pydantic.type
class Owner(pydantic.BaseModel):
    dog: Dog
```

A parametrized generic model, like `Page[User]`, can't be decorated: decorate a
subclass of it instead, and use the subclass for the field:

```python
from typing import Generic, TypeVar

T = TypeVar("T")


@strawberry.pydantic.type
class Page(pydantic.BaseModel, Generic[T]):
    items: list[T]


@strawberry.pydantic.type
class UserPage(Page[User]):
    pass


@strawberry.pydantic.type
class Directory(pydantic.BaseModel):
    users: UserPage
```
