---
title: Unsupported Inherited Field Error
---

# Unsupported Inherited Field Error

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

The same error is thrown when a `strawberry.pydantic` type inherits a field with
a resolver, like `label: str = strawberry.field(resolver=get_label)`, from a
regular Strawberry type or interface. Pydantic sees the annotation of the field,
and makes it a field of the model, with the resolver as its default value, so
the model would return the function as the value of `label`.

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

Declare fields with a resolver as methods with `@strawberry.field`, which
Pydantic doesn't see, so the model inherits them like any other method:

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

You can also declare the interface with `@strawberry.pydantic.interface`, and
the field with `@strawberry.pydantic.field`.
