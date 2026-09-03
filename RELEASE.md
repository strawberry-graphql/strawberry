---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Schemas can now use custom error loggers for
    GraphQL execution errors. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Schemas can now use custom error loggers to
    integrate GraphQL execution errors with application logging and observability.
---

This release adds support for custom GraphQL execution error loggers.

Pass a logger object to `strawberry.Schema(logger=...)` to control how execution
errors are reported without subclassing the schema. Existing schemas continue to
use the `strawberry.execution` logger by default.
