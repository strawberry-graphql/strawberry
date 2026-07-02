---
release type: patch
social_messages:
  x: >-
    {project_name} {version} fixes a bug where Datadog spans could be left open when an operation raised an exception.
  linkedin: >-
    {project_name} {version} fixes a bug in the Datadog tracing extension where spans could be left open indefinitely when a GraphQL operation raised an exception. Upgrade to get correct span lifecycle management in all error paths.
---

This release fixes a bug in the Datadog extension where spans could be left open indefinitely when a GraphQL operation raised an exception.

Strawberry now makes sure that the Datadog extension always closes spans,
also in the case of exceptions.
