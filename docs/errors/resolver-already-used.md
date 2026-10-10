---
title: Resolver Already Used Error
---

# Resolver Already Used Error

## Description

This error is thrown when the same function is used as the resolver of more than
one `strawberry.pydantic.field`, for example the following code will throw this
error:

```python
import pydantic
import strawberry


def get_label(self) -> str:
    return f"#{self.id}"


@strawberry.pydantic.type
class Ticket(pydantic.BaseModel):
    id: int

    label = strawberry.pydantic.field(get_label)


@strawberry.pydantic.type
class Issue(pydantic.BaseModel):
    id: int

    label = strawberry.pydantic.field(description="The issue label")(get_label)
```

This happens because `strawberry.pydantic.field` returns the function itself, so
that Pydantic ignores it, and stores the field's options on it. A function can
only hold the options of one field.

## How to fix this error

You can fix this error by giving each field its own function, which can call the
shared one:

```python
import pydantic
import strawberry


def get_label(self) -> str:
    return f"#{self.id}"


@strawberry.pydantic.type
class Ticket(pydantic.BaseModel):
    id: int

    label = strawberry.pydantic.field(get_label)


@strawberry.pydantic.type
class Issue(pydantic.BaseModel):
    id: int

    @strawberry.pydantic.field(description="The issue label")
    def label(self) -> str:
        return get_label(self)
```
