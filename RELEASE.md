---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Fields defined with typing.Annotated now
    support the full strawberry.field API across object, input, and interface
    types.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. You can now configure fields with
    strawberry.field inside typing.Annotated consistently across object, input,
    and interface types, including defaults and combined metadata.
---

This release fixes fields configured with `strawberry.field()` inside
`typing.Annotated`.

You can now use this syntax consistently on object types, input types, and
interfaces, including in projects that use `from __future__ import annotations`:

```python
from typing import Annotated

import strawberry

Name = Annotated[
    str,
    strawberry.field(name="displayName", default="Anonymous"),
]


@strawberry.type
class User:
    name: Name
```

All `strawberry.field()` options are supported. Fields with `default` or
`default_factory` can be omitted when creating an instance, and field
configuration can be combined with other Strawberry metadata such as named
unions.
