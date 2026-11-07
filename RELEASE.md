---
release type: patch
---

This release fixes how a `null` for a `strawberry.Maybe[T]` field of a
`@strawberry.pydantic.input` is reported.

Pydantic now validates the `null` as the type inside the `Maybe`, so it's
reported at the field, like `["input", "name"]`, together with the other
problems of the input, and returned as `ValidationError` data through
`PydanticValidationErrorHandler`:

```python
@strawberry.pydantic.input
class UpdateUserInput(BaseModel):
    name: strawberry.Maybe[Annotated[str, StringConstraints(min_length=1)]]
```

```json
{
  "location": ["input", "name"],
  "message": "Input should be a valid string",
  "type": "string_type"
}
```

Before, it failed the whole operation with a top-level error and `data: null`,
whether the `null` was written in the document or sent in a variable. Regular
`@strawberry.input` types are unchanged.

The docs now also cover `@model_validator` on `Maybe` fields, which sees them as
`None` or a `Some`, and `model_dump(exclude_none=True)`, which keeps a `Maybe`
field set to `null`.
