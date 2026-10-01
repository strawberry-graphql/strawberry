---
title: Resolver Field Overrides Model Field Error
---

# Resolver Field Overrides Model Field Error

## Description

This error is thrown when a resolver of a `strawberry.pydantic` type has the
same name as a field of the model it inherits from, for example the following
code will throw this error:

```python
import pydantic
import strawberry


class BaseUser(pydantic.BaseModel):
    name: str


@strawberry.pydantic.type
class User(BaseUser):
    @strawberry.pydantic.field
    def name(self) -> str:
        return "Ada"
```

This happens because Pydantic uses a method that overrides a field as the
default value of the field, instead of a method, so the resolver would never be
called.

## How to fix this error

You can fix this error by renaming the resolver, or by removing the model field:

```python
import pydantic
import strawberry


class BaseUser(pydantic.BaseModel):
    name: str


@strawberry.pydantic.type
class User(BaseUser):
    @strawberry.pydantic.field
    def display_name(self) -> str:
        return self.name.title()
```
