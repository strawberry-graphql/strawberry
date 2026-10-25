---
release type: patch
---

This release fixes `strawberry codegen` failing with a bare `AssertionError` (for
example `AssertionError: User,nmae`) when an operation doesn't match the schema.

Operations are now checked for unknown fields, types and fragments before code is
generated. `QueryCodegen.run` raises `InvalidOperationError` with the GraphQL
errors, and the CLI reports each one with its file and location:

```
Error: viewer.graphql:1:25: Cannot query field 'nmae' on type 'User'. Did you mean 'name'?
```
