---
title: Inherited Strawberry Resolver Error
---

# Inherited Strawberry Resolver Error

## Description

This error is thrown when a `strawberry.pydantic` type inherits a field with a
resolver from a regular Strawberry type or interface, for example the following
code will throw this error:

```python
import pydantic
import strawberry


def get_label() -> str:
    return "Label"


@strawberry.interface
class Labelled:
    label: str = strawberry.field(resolver=get_label)


@strawberry.pydantic.type
class Product(pydantic.BaseModel, Labelled):
    name: str
```

This happens because Pydantic sees the annotation of the field, and makes it a
field of the model, with the resolver as its default value. The model would then
return the function as the value of `label`, and fail to serialize it.

## How to fix this error

You can fix this error by declaring the field as a method with
`@strawberry.field`, which Pydantic doesn't see, so the model inherits it like
any other method:

```python
import pydantic
import strawberry


def get_label() -> str:
    return "Label"


@strawberry.interface
class Labelled:
    @strawberry.field
    def label(self) -> str:
        return get_label()


@strawberry.pydantic.type
class Product(pydantic.BaseModel, Labelled):
    name: str
```

Or declare the interface with `@strawberry.pydantic.interface`, and its resolver
with `@strawberry.pydantic.field`:

```python
import pydantic
import strawberry


@strawberry.pydantic.interface
class Labelled(pydantic.BaseModel):
    @strawberry.pydantic.field
    def label(self) -> str:
        return "Label"


@strawberry.pydantic.type
class Product(Labelled):
    name: str
```
