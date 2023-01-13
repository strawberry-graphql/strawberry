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

<Note>

`Annotated` is only available in Python 3.9+, if you are using an older version
of Python you can use `typing_extensions.Annotated` instead.

```python
# users.py
from typing import TYPE_CHECKING, List
from typing_extensions import Annotated

import strawberry

if TYPE_CHECKING:
    from .posts import Post


@strawberry.type
class User:
    name: str
    posts: List[Annotated["Post", strawberry.lazy(".posts")]]
```

</Note>
