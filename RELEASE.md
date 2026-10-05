---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes strawberry.lazy references
    to types re-exported through Python 3.15 native lazy imports. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes strawberry.lazy references
    to types re-exported through Python 3.15 native lazy imports, so schemas build
    without having to resolve those imports manually first.
---

This release fixes `strawberry.lazy` references to types re-exported through
Python 3.15 native lazy imports.

Strawberry now resolves these imports when building a schema, instead of passing
an unresolved import proxy to the schema converter. Both `lazy from` imports and
imports made lazy through `__lazy_modules__` are supported.
