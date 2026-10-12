---
title: Strawberry Field In Model Error
---

# Strawberry Field In Model Error

## Description

This error is thrown when a `strawberry.pydantic` type would get a field with a
resolver declared with `strawberry.field` outside of a Strawberry type, for
example in a Pydantic model that makes Pydantic ignore Strawberry fields, so
that it accepts `@strawberry.field`:

```python
import pydantic
import strawberry
from strawberry.types.field import StrawberryField


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(ignored_types=(StrawberryField,))

    name: str

    @strawberry.field
    def shout(self) -> str:
        return self.name.upper()
```

Pydantic types only read `strawberry.field` from regular Strawberry types and
interfaces. Without this error, the field would silently be missing from the
schema. The same error is thrown for `@strawberry.field` methods on a base class
that isn't decorated, which `@strawberry.type` ignores too.

## How to fix this error

You can fix this error by using `@strawberry.pydantic.field`, which adds fields
with a resolver to Pydantic types, and doesn't need any configuration:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field
    def shout(self) -> str:
        return self.name.upper()
```

For a base class that isn't a Pydantic model, you can also decorate it with
`@strawberry.type` or `@strawberry.interface`, as Pydantic types inherit the
fields with a resolver of regular Strawberry types and interfaces.
