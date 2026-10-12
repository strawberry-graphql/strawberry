---
title: Attribute Overrides Computed Field Error
---

# Attribute Overrides Computed Field Error

## Description

This error is thrown when a `strawberry.pydantic` type overrides a computed
field, inherited from a base model, with something that isn't a field, like a
method. For example the following code will throw this error:

```python
import pydantic
import strawberry


class User(pydantic.BaseModel):
    first_name: str
    last_name: str

    @pydantic.computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@strawberry.pydantic.type
class Admin(User):
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name} (admin)"
```

This happens because Pydantic keeps the inherited computed field, and uses the
method itself as its value, so neither the GraphQL field nor Pydantic's
serialization would work.

## How to fix this error

To change the value of the field, make the method a computed field too:

```python
import pydantic
import strawberry


class User(pydantic.BaseModel):
    first_name: str
    last_name: str

    @pydantic.computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@strawberry.pydantic.type
class Admin(User):
    @pydantic.computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name} (admin)"
```

A method decorated with `@strawberry.pydantic.field` replaces the computed field
with a field with a resolver, which can take arguments.

If the method isn't meant to be part of the GraphQL type, rename it, so that the
inherited computed field is kept.
