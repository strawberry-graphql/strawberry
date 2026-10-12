---
title: Unresolved Annotated Field Error
---

# Unresolved Annotated Field Error

## Description

This error is thrown when a field of a `strawberry.pydantic` type uses
`Annotated`, but its annotation uses names that aren't defined yet when the
model is decorated, for example the following code will throw this error:

```python
from __future__ import annotations

from typing import Annotated

import pydantic
import strawberry

from .permissions import IsAdmin


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    account: Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]
    savings: Annotated[Account | None, pydantic.Field(exclude=True)] = None


@strawberry.pydantic.type
class Account(pydantic.BaseModel):
    iban: str
```

This happens because Pydantic keeps the annotation of `account` as a string
until `Account` is defined, and only reads the options in `Annotated` then.
Strawberry reads the options when the model is decorated, so it can't see them:
the permissions of `strawberry.field()` wouldn't be checked, and the fields
excluded with `pydantic.Field(exclude=True)` would be exposed. Other options,
like descriptions and deprecations, would be lost too.

The same happens when the whole annotation is quoted, like
`account: "Annotated[Account, strawberry.field(...)]"`, or when it uses an alias
of an `Annotated` type, like `AdminOnly[Account]` with
`AdminOnly = Annotated[T, strawberry.field(permission_classes=[IsAdmin])]`.

The error is thrown for any field whose annotation Pydantic couldn't resolve yet
and that uses `Annotated` at any depth, like `Annotated[Account, ...] | None`,
directly or through an alias defined before the model. This includes options
that only Pydantic uses, like `pydantic.Field(min_length=1)`, validators like
`pydantic.AfterValidator(...)`, or constrained types like `pydantic.PositiveInt`
(an alias of `Annotated[int, Gt(0)]`): Pydantic would apply them once the model
is rebuilt, but Strawberry doesn't tell them apart from the options it uses, so
they need the same fix. `strawberry.lazy()`, `strawberry.union()` and
`strawberry.Private` are fine on their own, as Strawberry reads them when it
resolves the annotation.

## How to fix this error

You can fix this error by defining the models the annotation references before
the model:

```python
from __future__ import annotations

from typing import Annotated

import pydantic
import strawberry

from .permissions import IsAdmin


@strawberry.pydantic.type
class Account(pydantic.BaseModel):
    iban: str


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    account: Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]
    savings: Annotated[Account | None, pydantic.Field(exclude=True)] = None
```

If they can't be defined first, decorate the model once they're defined, after
letting Pydantic resolve its annotations with `model_rebuild()`:

```python
from __future__ import annotations

from typing import Annotated

import pydantic
import strawberry

from .permissions import IsAdmin


class User(pydantic.BaseModel):
    name: str
    account: Annotated[Account, strawberry.field(permission_classes=[IsAdmin])]
    savings: Annotated[Account | None, pydantic.Field(exclude=True)] = None


@strawberry.pydantic.type
class Account(pydantic.BaseModel):
    iban: str


User.model_rebuild()
strawberry.pydantic.type(User)
```

When the field is inherited, rebuild and decorate the model you expose, not the
model that declares the field: Pydantic doesn't rebuild subclasses.

### Models that reference each other

When two models reference each other with `Annotated` options, neither can be
defined first, and a model can only be decorated once the models its fields use
are decorated. Instead, quote only the types, in a module without
`from __future__ import annotations`: Python then evaluates the rest of the
annotation right away, so Pydantic reads the options when the model is created:

```python
from typing import Annotated

import pydantic
import strawberry

from .permissions import IsAdmin


@strawberry.pydantic.type
class User(pydantic.BaseModel):
    name: str
    posts: Annotated[list["Post"], strawberry.field(permission_classes=[IsAdmin])]
    drafts: Annotated[list["Post"], pydantic.Field(exclude=True)] = []


@strawberry.pydantic.type
class Post(pydantic.BaseModel):
    title: str
    author: Annotated[User, pydantic.Field(description="The author")]


User.model_rebuild()
```

The same works for types from other modules referenced with `strawberry.lazy()`,
like
`Annotated["Account", strawberry.lazy("app.accounts"), strawberry.field()]`. As
with any Pydantic model that uses a type defined later, call `model_rebuild()`
once the type is defined, before validating data with the model.
