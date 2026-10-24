---
title: Maybe Field Error
---

# Maybe Field Error

## Description

This error is thrown when a field of a `strawberry.pydantic.input` uses
`strawberry.Maybe`, for example the following code will throw this error:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class UpdateUserInput(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    name: strawberry.Maybe[str] = None
```

Without `arbitrary_types_allowed=True`, Pydantic itself raises an error for
`strawberry.Maybe` when the model is defined.

Pydantic doesn't know how to validate Strawberry's `Some` values, and the
integration does not currently support `strawberry.Maybe`.

## How to fix this error

Use a regular Strawberry input if you need to distinguish omission from an
explicit `null`. GraphQL fills in published defaults before Pydantic validates
an input, so `model_fields_set` and `model_dump(exclude_unset=True)` do not
identify only client-submitted fields.

```python
import strawberry


@strawberry.input
class UpdateUserInput:
    name: strawberry.Maybe[str | None]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_user(self, input: UpdateUserInput) -> str:
        if input.name is None:
            return "Name was omitted"

        return f"Name was supplied: {input.name.value!r}"
```
