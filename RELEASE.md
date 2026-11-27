---
release type: patch
---

This release fixes `strawberry.experimental.pydantic.type` (and the `input` /
`interface` helpers built on it) silently dropping user-defined attributes
from the decorated class.

The decorator rebuilds the class with `dataclasses.make_dataclass`, and only
`is_type_of`, custom `from_pydantic` / `to_pydantic` methods and
`resolve_reference` were carried over to the new class. Any other attribute
defined by the user, such as a `@staticmethod`, a `@classmethod`, a helper
method or a plain class attribute, was lost and raised `AttributeError` at
runtime. These attributes are now preserved on the resulting type.
