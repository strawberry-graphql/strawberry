---
release type: patch
social_messages:
  x: >-
    Strawberry {version} is out! This release fixes schema codegen silently
    renaming fields whose GraphQL names don't survive camel-casing. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    Strawberry {version} is out. This release fixes schema codegen so that
    GraphQL field names such as `some_field` or `allowCustomExportURL` keep
    their original names in the generated schema instead of being silently
    renamed.
---

This release fixes schema codegen silently renaming fields whose GraphQL names
are not reproduced by camel-casing.

Strawberry derives the GraphQL name of a field by camel-casing its Python name,
so generating `some_field` from a GraphQL field named `some_field` produced a
schema exposing `someField` instead. The same happened to names containing
acronyms, such as `allowCustomExportURL`, which came back as
`allowCustomExportUrl`.

Codegen now adds an explicit alias whenever camel-casing would not give the
original name back:

```python
@strawberry.type
class Example:
    some_field: int | None = strawberry.field(name="some_field")
    allow_custom_export_url: bool = strawberry.field(name="allowCustomExportURL")
```

Fields whose GraphQL names convert to the same Python name (for example
`someField` and `some_field`) are also no longer silently dropped.
