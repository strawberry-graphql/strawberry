---
release type: patch
---

This release adds internal helpers for reading `strawberry.field()` and other
options from `Annotated` annotations, so that integrations, like the upcoming
first-class Pydantic support, can share them with `@strawberry.type` instead of
reimplementing them.

- `strawberry.types.field.get_annotated_field()` splits an annotation like
  `Annotated[int, strawberry.field(name="age")]` into its type and its
  `strawberry.field()`, and raises an error for a `strawberry.field()` used twice
  or nested in the type.
- `strawberry.types.unresolved_annotations.find_unresolved_options()` reports
  why the options of an annotation that can't be evaluated yet, for example
  because it uses a type defined further down the module, can't be read. It
  checks `strawberry.field()` by default, and integrations can pass the options
  they read themselves.

There are no changes in behavior.
