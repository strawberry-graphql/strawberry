---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Schema extensions can now use
    strawberry.Info, with a compatibility warning and codemod for legacy
    GraphQLResolveInfo hooks. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Schema extension resolvers can now opt into
    strawberry.Info, including custom Info classes, while a codemod provides a
    behavior-preserving migration from GraphQLResolveInfo.
---

This release adds `strawberry.Info` support to schema extension resolvers.

Annotating `SchemaExtension.resolve` with `strawberry.Info` now passes the same
configured Info type used by field resolvers. Existing unannotated and
`GraphQLResolveInfo` extension resolvers continue to receive the graphql-core
object, with a deprecation warning ahead of Strawberry 1.0.

Strawberry's built-in tracing extensions now receive `strawberry.Info` too. Subclasses that override `resolve`, or `add_tags` and
`filter_resolver_args` on `OpenTelemetryExtension`, must pass `strawberry.Info`
to their `super()` calls. The OpenTelemetry `arg_filter` callback still receives
`GraphQLResolveInfo`.

Run `strawberry upgrade schema-extension-info .` to opt direct subclasses of
`SchemaExtension` and of the built-in extensions into Strawberry Info while
preserving their existing raw Info behavior.
