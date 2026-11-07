---
release type: patch
---

This release fixes `strawberry codegen` wrapping nullable `strawberry.Maybe`
input fields twice. A field declared as `strawberry.Maybe[str | None]` was
generated as `Optional[Optional[str]]` in Python and `string | undefined | undefined`
in TypeScript. It's now `Optional[str]` and `string | undefined`, matching the
nullable `String` it is in the schema.
