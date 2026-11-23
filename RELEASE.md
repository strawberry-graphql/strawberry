---
release type: patch
---

This release fixes schema-codegen dropping field arguments from generated types.

Fields with arguments are now emitted as resolvers with matching parameters (and defaults), so the generated schema matches the SDL and input types that are only referenced through arguments stay reachable. This also fixes `strawberry codegen` failing with a bare `AssertionError` when run against a schema produced by schema-codegen whose operations use those input types.
