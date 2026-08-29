---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release reports misplaced nested
    strawberry.field() metadata instead of silently ignoring it.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release reports misplaced nested
    strawberry.field() metadata with a clear error instead of silently ignoring it.
---

This release fixes silently ignored `strawberry.field()` metadata in nested type
annotations.

Strawberry now raises a clear error when field metadata is placed below the
class-field annotation, such as on a list item, and explains that it must be moved
to the outermost `Annotated` metadata for the field.

For example, Strawberry now reports this misplaced metadata:

```python
from typing import Annotated

import strawberry


@strawberry.type
class Query:
    names: list[Annotated[str, strawberry.field(description="A name")]]
```

Move `strawberry.field()` to the field's outermost `Annotated` metadata:

```python
@strawberry.type
class Query:
    names: Annotated[list[str], strawberry.field(description="The names")]
```
