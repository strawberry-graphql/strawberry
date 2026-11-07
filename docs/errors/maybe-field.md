---
title: Maybe Field Error
---

# Maybe Field Error

## Description

This error is thrown when a field of a Pydantic model uses `strawberry.Maybe` in
a way the integration doesn't support:

- on a `@strawberry.pydantic.type` or `@strawberry.pydantic.interface`, as
  `Maybe` is for inputs: GraphQL has no value for an output field that was left
  out;
- on a `@strawberry.pydantic.input`, with a default other than `None`, or a
  default factory;
- on a `@strawberry.pydantic.input`, with Pydantic metadata outside the `Maybe`,
  like `Annotated[strawberry.Maybe[int], Field(ge=0)]` or
  `strawberry.Maybe[int] = Field(None, ge=0)`: Pydantic would apply the
  constraints to the `strawberry.Some`, not to the value in it;
- on a `@strawberry.pydantic.input`, with an `after` or `plain`
  `@field_validator` naming the field: an `after` validator would get the
  `strawberry.Some`, and a `plain` one would replace the validation of the
  `Maybe`;
- on a `@strawberry.pydantic.input`, with an explicit `None` default that
  Pydantic validates, because of `validate_default`.

For example, the following code throws this error:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class UpdateUserInput(pydantic.BaseModel):
    name: strawberry.Maybe[str] = "Ada"
```

## How to fix this error

On an input, remove the default: a `Maybe` field is `None` when the client
leaves it out, and a `strawberry.Some` with the value when it sends one.
Pydantic validates the value inside the `Some`, and doesn't validate the `None`
the field gets when it's left out.

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class UpdateUserInput(pydantic.BaseModel):
    name: strawberry.Maybe[str]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_user(self, input: UpdateUserInput) -> str:
        if input.name is None:
            return "Name was omitted"

        return f"Name was supplied: {input.name.value!r}"
```

Put constraints and validators in the type inside the `Maybe`, where they apply
to the value. A `@field_validator` with `mode="before"` or `mode="wrap"` works
too, as it gets the value the client sent:

```python
from typing import Annotated

import pydantic
import strawberry


def check_name(name: str) -> str:
    return name.strip()


@strawberry.pydantic.input
class UpdateUserInput(pydantic.BaseModel):
    age: strawberry.Maybe[Annotated[int, pydantic.Field(ge=0)]]
    name: strawberry.Maybe[Annotated[str, pydantic.AfterValidator(check_name)]]
```

On a type or an interface, make the field nullable instead:

```python
import pydantic
import strawberry


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str | None
```
