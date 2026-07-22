---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! FastAPI GraphQLRouter subclasses now accept
    valid custom context getters without extra generic annotations. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. FastAPI GraphQLRouter subclasses now
    type-check with valid custom context getters even when they omit explicit
    generic parameters.
---

This release fixes type checking for FastAPI `GraphQLRouter` subclasses that
provide a custom context getter without explicit generic parameters.

Bare subclasses now default to the context types supported by the FastAPI
integration, so valid context getters are accepted by type checkers. Explicitly
using `GraphQLRouter[MyContext]` is still available when the precise context
type needs to be preserved on the subclass.

The minimum supported `typing-extensions` version is now 4.14.0, ensuring these
default generic parameters work across Strawberry's supported Python versions.
