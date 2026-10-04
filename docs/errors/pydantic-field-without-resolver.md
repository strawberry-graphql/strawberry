---
title: Pydantic Field Without Resolver Error
---

# Pydantic Field Without Resolver Error

## Description

This error is thrown when `strawberry.pydantic.field` is used on a field of a
Pydantic model instead of on a method, for example the following code will throw
this error:

```python
from typing import Annotated

import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    age: Annotated[int, strawberry.pydantic.field(name="yearsOld")]
```

Assigning it as the default value, like
`age: int = strawberry.pydantic.field(name="yearsOld")`, or nesting it in the
annotation, like `Optional[Annotated[int, strawberry.pydantic.field()]]`, throws
this error too.

This happens because `strawberry.pydantic.field` only adds fields with a
resolver: it decorates methods of the model, and its options would be ignored on
a model field.

## How to fix this error

You can fix this error by using `strawberry.field()` in the annotation of the
field instead:

```python
from typing import Annotated

import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    age: Annotated[int, strawberry.field(name="yearsOld")]
```

Keep `strawberry.pydantic.field` for methods that resolve a field:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str

    @strawberry.pydantic.field(description="The name in capital letters")
    def shout(self) -> str:
        return self.name.upper()
```
