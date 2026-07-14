---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Fields annotated with `None` now work with
    `strawberry.field()`. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Fields annotated with `None` now work when
    declared with `strawberry.field()`, matching other Void field declarations.
---

This release fixes schema generation for fields annotated with `None` and declared
with `strawberry.field()`. They now produce the `Void` scalar instead of raising
`UnresolvedFieldTypeError`.
