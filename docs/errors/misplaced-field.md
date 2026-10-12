---
title: Misplaced Field Error
---

# Misplaced Field Error

## Description

This error is thrown when `strawberry.field()` is assigned to a field of a
`strawberry.pydantic` type, for example the following code will throw this
error:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    email: str = strawberry.field(description="The user's email")
```

This happens because Pydantic treats the `strawberry.field()` like a dataclass
field: it keeps its default value and discards the rest of its options, like
descriptions and permissions.

The same error is thrown when:

- `strawberry.pydantic.field` is used on a field of the model, in its annotation
  or as its default value, like
  `age: Annotated[int, strawberry.pydantic.field(name="yearsOld")]`.
  `strawberry.pydantic.field` only adds fields with a resolver, so its options
  would be ignored.
- a method is decorated with `@strawberry.field` in a base class that isn't
  decorated, or in a Pydantic model that makes Pydantic ignore Strawberry fields
  with `ignored_types`. Pydantic types only read `@strawberry.field` methods
  from regular Strawberry types and interfaces, so the field would silently be
  missing from the schema.

## How to fix this error

You can fix this error by customizing the fields of the model with
`strawberry.field()` in their annotation, and adding fields with a resolver with
`@strawberry.pydantic.field`:

```python
from typing import Annotated

import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    email: Annotated[str, strawberry.field(description="The user's email")]
    age: Annotated[int, strawberry.field(name="yearsOld")]

    @strawberry.pydantic.field
    def shout(self) -> str:
        return self.name.upper()
```
