---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! On Python 3.14, strawberry.field() options
    in Annotated that use names defined later, like permission classes, now
    raise a clear error instead of breaking later.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. On Python 3.14, strawberry.field() options
    in Annotated that use names defined later in the module, like permission
    classes, directives, extensions or defaults, now raise a clear error when
    the type is created, instead of failing when the schema is built or being
    silently wrong.
---

This release fixes `strawberry.field()` options in `Annotated` that use names
that aren't defined yet when the type is created, on Python 3.14. For example, a
permission class defined after the type:

```python
from __future__ import annotations

from typing import Annotated

import strawberry


@strawberry.type
class User:
    account: Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]


class IsAdmin(BasePermission): ...
```

In modules with `from __future__ import annotations`, Strawberry reads these
annotations partially on Python 3.14, so the options got forward references
instead of the names they use. Depending on the option, building the schema then
failed with an unclear `TypeError` or `AttributeError`, a query failed, or the
option was silently wrong, like a description or a directive argument. This now
raises an `UnresolvedStrawberryFieldError` when the type is created, like on older
Python versions, which says to define the names the options use before the type.
