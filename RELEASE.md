---
release type: patch
---

This release fixes custom directives that take an `info` argument when they are
used on introspection fields such as `__typename`.

Their `Info` now describes the introspection field, so `info.python_name`,
`info.return_type` and `info.get_argument_definition()` work instead of raising
`AttributeError`.
