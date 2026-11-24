---
title: Ignored Serializer Error
---

# Ignored Serializer Error

## Description

This error is thrown when a `strawberry.pydantic` type or interface customizes
how its fields are serialized, for example the following code will throw this
error:

```python
from datetime import datetime

import pydantic
import strawberry


@strawberry.pydantic.type
class Event(pydantic.BaseModel):
    name: str
    starts_at: datetime

    @pydantic.field_serializer("starts_at")
    def as_date(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d")
```

This happens because GraphQL resolves the fields of Pydantic types from the
model's attributes, not from `model_dump()`, so the serializer would silently be
ignored: `startsAt` would return the full date and time. Serializers are often
used to hide or redact values, so ignoring them could expose data that the model
doesn't show anywhere else.

The same error is thrown for fields with a `PlainSerializer` or a
`WrapSerializer`, including inside their type, like
`list[Annotated[str, PlainSerializer(...)]]`, for fields with
`Field(exclude_if=...)`, and for models with a `@model_serializer`. This also
includes `PlainSerializer` and `WrapSerializer` in exposed computed fields'
return annotations. Fields that aren't part of the GraphQL type, like
`strawberry.Private` fields, can have serializers, and so can inputs, which
aren't serialized.

## How to fix this error

To change the value GraphQL returns, use a field with a resolver, or a custom
scalar:

```python
from datetime import date, datetime

import pydantic
import strawberry


@strawberry.pydantic.type
class Event(pydantic.BaseModel):
    name: str
    starts_at: strawberry.Private[datetime]

    @strawberry.pydantic.field
    def starts_on(self) -> date:
        return self.starts_at.date()
```

To hide a value, use `strawberry.Private` or `Field(exclude=True)`.

There is no configuration option to bypass this check. If serializers are needed
for another API, keep them on a separate model rather than on fields exposed by
the GraphQL type or interface.
