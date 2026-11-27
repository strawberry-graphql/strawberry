---
release type: patch
---

This release fixes schema printing for schema directives that take input objects, including `@strawberry.pydantic.input` models.

Directive arguments now go through the schema converter's input value conversion instead of `dataclasses.asdict`, so Pydantic input instances no longer fail with `TypeError` and renamed fields, `Maybe`/`Some` values, and `to_input` hooks are handled the same way as argument defaults.
