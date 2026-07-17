---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Custom scalar `serialize`/`parse_value`/`parse_literal`
    are now typed with graphql-core's aliases, so `strawberry.scalar(...)` type-checks
    cleanly under strict checkers. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Custom scalar callables (`serialize`, `parse_value`,
    `parse_literal`) are now typed with graphql-core's `GraphQLScalarSerializer`,
    `GraphQLScalarValueParser` and `GraphQLScalarLiteralParser` aliases instead of bare
    `Callable`, so `strawberry.scalar(...)` calls type-check cleanly under strict type
    checkers.
---

This release adds precise type annotations for custom scalars: `serialize`,
`parse_value` and `parse_literal` are now typed with graphql-core's
`GraphQLScalarSerializer`, `GraphQLScalarValueParser` and
`GraphQLScalarLiteralParser` aliases instead of bare `Callable`, so
`strawberry.scalar(...)` calls type-check cleanly under strict type checkers.
