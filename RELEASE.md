---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! This release adds lifecycle hooks for input
    objects. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds lifecycle hooks for input
    objects so inputs can validate and prepare request-scoped data before resolvers run.
---

This release adds lifecycle hooks for input objects.

Input objects can now define a synchronous or asynchronous `clean` method that
receives the resolver `Info` object after GraphQL input coercion and before
resolver execution.
