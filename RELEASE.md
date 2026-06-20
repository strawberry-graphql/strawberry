---
release type: patch
---

This release fixes compatibility with graphql-core 3.3 release candidates.

Strawberry now handles graphql-core's renamed custom executor hook and nullable
AST argument and directive collections, so schemas using custom execution
contexts and `Info.selected_fields` continue to work when testing against
graphql-core 3.3.
