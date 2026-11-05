---
release type: minor
---

This release adds a `sort_schema` option to `StrawberryConfig`.

When enabled, the GraphQL schema is sorted lexicographically. This affects
both introspection queries and exported schemas, making them easier to read
and diff.
