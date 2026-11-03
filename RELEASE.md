---
release type: patch
---

This release fixes an issue where running `strawberry codegen` crashed with
`AssertionError: Scalar type must have a python type` when custom scalars were
registered via `StrawberryConfig.scalar_map`.

`QueryCodegen` now correctly preserves and propagates the custom scalar's underlying
Python type (or falls back to `Any` when unmapped) when generating Python and
TypeScript client types.
