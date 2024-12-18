from typing import Annotated, TypeVar

from strawberry.utils.typing import type_has_annotation


class StrawberryPrivate: ...


T = TypeVar("T")

Private = Annotated[T, StrawberryPrivate()]
"""Represents a field that won't be exposed in the GraphQL schema.

Example:

```python
import strawberry


@strawberry.type
class User:
    name: str
    age: strawberry.Private[int]
```
"""


def is_private(type_: object) -> bool:
    return type_has_annotation(type_, StrawberryPrivate)


__all__ = ["Private", "is_private"]
