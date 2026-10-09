---
title: Lazy Types
---

# Lazy Types

Strawberry supports lazy types, which are useful when you have circular
dependencies between types.

For example, let's say we have a `User` type that has a list of `Post` types,
and each `Post` type has a `User` field. In this case, we can't define the
`User` type before the `Post` type, and vice versa.

To solve this, we can use lazy types:

```python
# posts.py
from typing import TYPE_CHECKING, Annotated

import strawberry

if TYPE_CHECKING:
    from .users import User


@strawberry.type
class Post:
    title: str
    author: Annotated["User", strawberry.lazy(".users")]
```

```python
# users.py
from typing import TYPE_CHECKING, Annotated, List

import strawberry

if TYPE_CHECKING:
    from .posts import Post


@strawberry.type
class User:
    name: str
    posts: List[Annotated["Post", strawberry.lazy(".posts")]]
```

`strawberry.lazy` in combination with `Annotated` allows us to define the path
of the module of the type we want to use, this allows us to leverage Python's
type hints, while preventing circular imports and preserving type safety by
using `TYPE_CHECKING` to tell type checkers where to look for the type.

## Python 3.15 lazy imports

On Python 3.15+, `strawberry.lazy` can reference a module that re-exports a type
using Python's native lazy imports:

```python
# exported_types.py (Python 3.15+)
lazy from .users import User
```

Use `Annotated["User", strawberry.lazy(".exported_types")]` to reference this
re-export. Strawberry resolves the native lazy import when it needs the type to
build the schema. This also works for imports made lazy through
`__lazy_modules__`.
