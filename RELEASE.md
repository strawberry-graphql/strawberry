---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Strawberry fields and arguments can now use
    typing.Literal, with allowed input values checked before resolvers run. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Strawberry fields and arguments can now use
    typing.Literal annotations. Literal values map to their underlying GraphQL
    scalar, and Strawberry validates inputs before calling resolvers.
---

This release adds support for using `typing.Literal` annotations in Strawberry
fields and arguments.

Homogeneous string, integer, and boolean literals map to their underlying
GraphQL scalar type. Strawberry validates input values against the allowed
literal values before calling the resolver, including literals nested inside
input objects, lists, and optional fields.

GraphQL introspection exposes the underlying scalar rather than the allowed
values. Applications that need clients to discover the available choices from
the schema should continue to use Strawberry enums. Mixed or unsupported literal
value types produce an error when the schema is created.
