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
object, with a deprecation warning ahead of Strawberry 2.

Run `strawberry upgrade schema-extension-info .` to opt direct schema extension
subclasses into Strawberry Info while preserving their existing raw Info
behavior.
