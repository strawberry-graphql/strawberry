---
release type: patch
---

This release fixes `strawberry schema-codegen` generating a module that fails
to import with a `NameError` when an input field's default value is a member of
an enum declared later in the schema, like `input SortInput { nulls: Nulls = last }`
followed by `enum Nulls`.

Enums used as input field defaults are now emitted before the inputs that use
them.
