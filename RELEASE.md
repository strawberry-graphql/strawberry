---
release type: patch
---

This release fixes a `TypeError` raised when decorating an enum with
`strawberry.enum` if a member uses `strawberry.enum_value` with an unhashable
value, such as a list.
