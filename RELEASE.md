---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release reduces execution overhead for
    plain fields and no-argument resolvers that do not request Info.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Strawberry now does less work when resolving
    plain fields and no-argument resolvers that do not request Info, reducing
    overhead when returning collections of objects.
---

This release fixes unnecessary execution overhead for plain fields and
no-argument resolvers that do not request `Info`.

Plain fields avoid temporary argument containers. Standard no-argument
resolvers without field extensions or applicable exception handlers skip
argument conversion and only construct `Info` when requested. Custom field
subclasses retain their existing resolution behavior.
