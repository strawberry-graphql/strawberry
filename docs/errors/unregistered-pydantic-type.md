---
title: Unregistered Pydantic Type Error
---

# Unregistered Pydantic Type Error

## Description

This error is thrown during schema construction when a field uses a Pydantic
model that is neither a Strawberry type nor registered in the schema's
`scalar_map`. It applies to regular Strawberry fields as well as fields of
`strawberry.pydantic` types (with Pydantic 2.11 or newer):

```python
import pydantic
import strawberry


class Address(pydantic.BaseModel):
    street: str


@strawberry.type
class Query:
    @strawberry.field
    def address(self) -> Address:
        return Address(street="Main Street")


schema = strawberry.Schema(query=Query)
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

A parametrized generic model, like `Page[User]`, is a GraphQL type when its
generic model is decorated, so decorate the generic model:

```python
from typing import Generic, TypeVar

T = TypeVar("T")


@strawberry.pydantic.type
class Page(pydantic.BaseModel, Generic[T]):
    items: list[T]


@strawberry.pydantic.type
class Directory(pydantic.BaseModel):
    users: Page[User]
```
