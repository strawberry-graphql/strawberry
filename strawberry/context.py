from typing import Annotated, TypeVar


class StrawberryContext: ...


T = TypeVar("T")

Context = Annotated[T, StrawberryContext()]
"""Represents a parameter holding the context of the current request.

Annotating a resolver parameter with `strawberry.Context[...]` passes the
request's context to it directly, without going through `info.context`. Type
checkers see the parameter as the type given in brackets.

Example:

```python
import strawberry
from dataclasses import dataclass


@dataclass
class MyContext:
    user_id: str


@strawberry.type
class Query:
    @strawberry.field
    def user_id(self, context: strawberry.Context[MyContext]) -> str:
        return context.user_id
```
"""


__all__ = ["Context", "StrawberryContext"]
