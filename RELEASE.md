---
release type: patch
---

This release fixes a resolver error when a plain `@strawberry.type` subclasses
a `strawberry.experimental.pydantic` type and the resolver returns an instance
of a sibling subclass. The inherited `is_type_of` now accepts instances of
the type it was defined for (and its pydantic model), instead of only
instances of the subclass accessing it.

Explicit `strawberry.cast` targets on plain subclasses keep working.
