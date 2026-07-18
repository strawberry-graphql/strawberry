---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! The `JSON` scalar docs now cover using
    ordinary Python types with `graphql_type` for both return values and input
    arguments, so resolvers type-check cleanly under mypy, pyright, and ty. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. The `JSON` scalar documentation now shows
    how to use ordinary Python types (dict, list, str, int, float, bool, None)
    with the `JSON` scalar via the existing `graphql_type` override, covering
    both resolver return values and input arguments. This lets resolvers
    type-check cleanly under mypy, pyright, and ty while still exposing the
    `JSON` scalar in the schema, without changing the `JSON` declaration or
    breaking `JSON(value)` constructor usage.
---

The `JSON` scalar documentation now shows how to use ordinary Python types
(`dict`, `list`, `str`, `int`, `float`, `bool`, `None`) with the `JSON` scalar
via the existing `graphql_type` override, covering both resolver return values
and input arguments. This lets resolvers type-check cleanly under mypy, pyright,
and ty while still exposing the `JSON` scalar in the schema, without changing
the `JSON` declaration or breaking `JSON(value)` constructor usage.

The scalar's mapping description was also corrected from "Python's `dict`" to
"ordinary JSON-compatible Python values" to match the identity serialize/parse
implementation.
