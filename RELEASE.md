---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes federated schemas with
    fields that return Query. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Fields can now return Query in federated
    schemas, allowing mutation results to expose queries without duplicate type
    errors.
---

This release fixes federated schemas with fields that return the Query type.

Mutation results and other object types can now reference Query without causing
a duplicate type error during schema construction.
