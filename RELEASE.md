Release type: patch

This release type improves support for strawberry.field in mypy,
now we don't get `Attributes without a default cannot follow attributes with one`
when using strawberry.field before a type without a default.
