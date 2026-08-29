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
allowed locations, repeatability, and any input types it uses.

A directive reused across the schema is defined only once. Input, enum, and scalar
types referenced by directive arguments are now part of the schema and may appear
in generated SDL even when they are not used by fields.
