---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Custom schema directives attached to types and
    fields now appear in GraphQL introspection. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. GraphQL tools can now discover custom schema
    directives attached throughout a Strawberry schema using standard
    introspection. 🍓
---

This release fixes introspection for custom schema directives.

Schema directives attached to types, fields, arguments, and other schema elements
now appear in standard GraphQL introspection. Schema explorers, IDEs, code
generators, and other tools can discover each directive's description, arguments,
allowed locations, repeatability, and any input types it uses. Federation directives,
including generated `@link` and `@composeDirective` applications, are discoverable
in the same way.

Federation directives and custom composed directives used on field arguments are
also included in the generated subgraph metadata, so routers can recognize those
argument annotations without additional schema configuration.

A directive reused across the schema is defined only once. Input, enum, and scalar
types referenced by directive arguments are now part of the schema and may appear
in generated SDL even when they are not used by fields.

Because these directives and argument types are now part of the runtime schema,
their GraphQL names must be unique. Schema construction reports a clear error when
different directive definitions share a name, a custom directive replaces a
built-in directive such as `@skip`, or a directive argument type conflicts with
another schema type. Compatible custom `@oneOf` definitions continue to use
GraphQL's built-in directive.
