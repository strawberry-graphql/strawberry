from collections.abc import AsyncGenerator
from typing import Annotated, TypeVar


class StrawberryStreamable: ...


T = TypeVar("T")

Streamable = Annotated[AsyncGenerator[T, None], StrawberryStreamable()]
"""Represents a list that can be streamed using @stream.

Example:

```python
import strawberry


@strawberry.type
class Comment:
    id: strawberry.ID
    content: str


@strawberry.type
class Article:
    @strawberry.field
    @staticmethod
    async def comments() -> strawberry.Streamable[Comment]:
        for comment in fetch_comments():
            yield comment
```
"""

__all__ = ["Streamable"]
