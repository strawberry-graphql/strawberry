---
release type: patch
---

This release fixes `strawberry.Maybe` fields on output types: a `Maybe` field on
a `@strawberry.type` or `@strawberry.interface`, or a resolver returning one,
also inside a list like `list[strawberry.Maybe[str]]`, now raises
`MaybeFieldOnOutputTypeError` when the schema is built, instead of silently
serializing the `strawberry.Some` as its repr, like `"Some('Ada')"`. `Maybe` is
for inputs: make the field nullable instead.

`@strawberry.pydantic.type` and `@strawberry.pydantic.interface` raise the same
error for `Maybe` fields, instead of `MaybeFieldError`.
