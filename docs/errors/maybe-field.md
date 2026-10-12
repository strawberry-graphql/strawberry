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

This happens because Pydantic doesn't know about `strawberry.Maybe`, and has its
own way to tell omitted fields apart from explicit `null` values.

## How to fix this error

You can fix this error by giving the field a `None` default, and using
`model_fields_set` (or `model_dump(exclude_unset=True)`) to find the fields that
the client sent:

```python
import pydantic
import strawberry


@strawberry.pydantic.input
class UpdateUserInput(pydantic.BaseModel):
    name: str | None = None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_user(self, input: UpdateUserInput) -> str:
        changes = input.model_dump(exclude_unset=True)

        return f"Updated: {sorted(changes)}"
```
