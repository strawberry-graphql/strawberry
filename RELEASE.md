---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Operation directive resolvers now receive
    correctly typed arguments, including inputs, enums, custom scalars, and
    defaults. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Operation directive arguments now behave
    like field arguments, with standard GraphQL coercion and Strawberry input
    conversion for literals, variables, defaults, and explicit null values. 🍓
---

This release fixes argument handling for operation directive resolvers.

Arguments passed to operation directives now use GraphQL's standard coercion before
your resolver runs. Directive resolvers receive Python numeric values, Strawberry
enum members and nested input objects, and values parsed by custom scalars, whether
clients use literals or variables.

When a client omits a variable, Strawberry now applies the directive argument's
default. Explicit `null` continues to reach nullable arguments as `None`.
