---
release type: minor
---

This release adds `Info.field_args`, a cached property that returns the arguments
passed to the current field, already converted to Strawberry types. Scalars are
coerced and input types are converted to their proper dataclasses, mirroring the
values a resolver receives. Both inline literals and variables are handled, and
arguments that were not provided are omitted.
