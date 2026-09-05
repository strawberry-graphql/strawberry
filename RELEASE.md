---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Object and input types can now be declared
    with `extend=True` alongside a base type of the same name, so separate
    modules can contribute fields to one GraphQL type. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds GraphQL object and input
    object type extensions: several Python classes can now share a single
    GraphQL type name with `extend=True`, letting independent modules each
    contribute fields to the same type. The generated SDL prints the extensions
    as `extend type` and `extend input`.
---

This release adds support for GraphQL object and input object type extensions.

`@strawberry.type(..., extend=True)` and `@strawberry.input(..., extend=True)`
can now be registered alongside a base type with the same GraphQL name. The
generated SDL prints extension definitions as `extend type` and `extend input`,
and input extension fields are available on converted resolver arguments.
Schema directives attached to extension types and fields are included in
introspection as well as the printed SDL.
