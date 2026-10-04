---
title: Unresolved Strawberry Field Error
---

# Unresolved Strawberry Field Error

## Description

This error is raised on Python 3.10 to 3.13 when a field's annotation has
`strawberry.field()` options, but uses a type that isn't defined yet when the
Strawberry type is created. For example, a type defined further down the module,
in a module with `from __future__ import annotations`:

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

Strawberry reads the `strawberry.field()` options when the type is created, but
before Python 3.14 it can't evaluate an annotation that uses names that aren't
defined yet. The type itself is resolved later, when the schema is built, so
instead of silently ignoring options like the permissions above, Strawberry
raises this error.

The same applies to a shared field, like `Annotated[Account, ADMIN_ONLY_FIELD]`,
and to an `Annotated` alias with `strawberry.field()`, like
`AdminOnly[Account]`.

## How to fix this error

Pass the options as the field's default instead of in `Annotated`. This works
for any type, including types that reference themselves:

```python
from __future__ import annotations

import strawberry


@strawberry.type
class User:
    account: Account = strawberry.field(permission_classes=[IsAdmin])


@strawberry.type
class Account:
    iban: str
```

Or define the types the annotation uses before the type that uses them:

```python
from __future__ import annotations

from typing import Annotated

import strawberry


@strawberry.type
class Account:
    iban: str


@strawberry.type
class User:
    account: Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]
```

Or use `strawberry.lazy()` for the type, for example for types only imported
under `TYPE_CHECKING`. It works together with `strawberry.field()`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import strawberry

if TYPE_CHECKING:
    from .accounts import Account


@strawberry.type
class User:
    account: Annotated[
        Account,
        strawberry.lazy(".accounts"),
        strawberry.field(permission_classes=[IsAdmin]),
    ]
```

Python 3.14 and newer read the options of these annotations without any change.

An `Annotated` alias with `strawberry.field()`, like `AdminOnly[Account]`, has
to be defined before the types that use it, on every Python version.
