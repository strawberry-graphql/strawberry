Release type: minor

This release adds `strawberry.lazy` which allows you to define the type of the
field and its path. This is useful when you want to define a field with a type
that has a circular dependency.

For example, let's say we have a `User` type that has a list of `Post` and a
`Post` type that has a `User`:

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
