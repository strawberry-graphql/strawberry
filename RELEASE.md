---
release type: minor
---

This release adds support for `strawberry.Maybe` on the fields of
`@strawberry.pydantic.input` models, to tell the fields a client left out apart
from the ones it set to `null`, like on other input types:

```python
@strawberry.pydantic.input
class UpdateUserInput(pydantic.BaseModel):
    name: strawberry.Maybe[Annotated[str, StringConstraints(min_length=1)]]
    nickname: strawberry.Maybe[str | None]
```

A `Maybe` field is `None` when the client leaves it out, and a `strawberry.Some`
with the validated value when it sends one, so `model_dump(exclude_unset=True)`
only has the fields the client sent. Pydantic validates the value inside the
`Maybe`, and reports errors at the field, like `["input", "name"]`. `Maybe[T]`
doesn't accept `null`, while `Maybe[T | None]` gives `Some(None)` for it. The
fields don't need a default, and `Maybe` still can't be used on output types.
