---
release type: patch
---

This release fixes `strawberry.experimental.pydantic` types and inputs dropping
field descriptions set via `strawberry.field(description=...)`. An explicit
description now wins over the pydantic field's own description, which is still
used when no explicit one is given.
