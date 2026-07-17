---
release type: patch
---

This release improves type annotations for custom scalars: `serialize`,
`parse_value` and `parse_literal` are now typed with graphql-core's
`GraphQLScalarSerializer`, `GraphQLScalarValueParser` and
`GraphQLScalarLiteralParser` aliases instead of bare `Callable`, so
`strawberry.scalar(...)` calls type-check cleanly under strict type checkers.
