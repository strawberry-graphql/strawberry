---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes strawberry.field()
    options, like permissions, being silently ignored on Python 3.10 to 3.13 for
    fields whose type is defined later in the module.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes strawberry.field()
    options in Annotated, like permission classes, being silently ignored on
    Python 3.10 to 3.13 when the field's type is defined later in the module.
    Strawberry now raises a clear error with the ways to fix it.
---

This release fixes `strawberry.field()` options in `Annotated` being silently
ignored on Python 3.10 to 3.13, when the field's type isn't defined yet when the
Strawberry type is created. For example, with a type defined further down the
module:

```python
from __future__ import annotations

from typing import Annotated

import strawberry


@strawberry.type
class User:
    account: Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]


@strawberry.type
class Account:
    iban: str
```

Strawberry couldn't evaluate the annotation when `User` was created, so it
skipped its options and resolved `Account` later, when building the schema. The
field was still in the schema, but without its permissions, name, description or
default. Strawberry now raises an `UnresolvedStrawberryFieldError` instead. To
fix it, pass the options as the field's default
(`account: Account = strawberry.field(permission_classes=[IsAdmin])`), define
`Account` before `User`, or use `strawberry.lazy()` for the type.

Python 3.14 and newer already read these options, and aren't affected.
