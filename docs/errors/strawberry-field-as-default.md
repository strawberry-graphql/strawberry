---
title: Strawberry Field As Default Error
---

# Strawberry Field As Default Error

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

## How to fix this error

You can fix this error by moving the `strawberry.field()` into the annotation,
with `Annotated`:

```python
from typing import Annotated

import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    email: Annotated[str, strawberry.field(description="The user's email")]
```
