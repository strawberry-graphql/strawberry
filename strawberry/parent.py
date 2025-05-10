import re
from typing import Annotated, Any, ForwardRef, TypeVar

_parent_re = re.compile(r"^(?:strawberry\.)?Parent\[(.*)\]$")


class StrawberryParent: ...


T = TypeVar("T")

Parent = Annotated[T, StrawberryParent()]
"""Represents a parameter holding the parent resolver's value.

This can be used when defining a resolver on a type when the parent isn't expected
to return the type itself.

Example:

```python
import strawberry
from dataclasses import dataclass


@dataclass
class UserRow:
    id_: str


@strawberry.type
class User:
    @strawberry.field
    @staticmethod
    async def name(parent: strawberry.Parent[UserRow]) -> str:
        return f"User Number {parent.id_}"


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return UserRow(id_="1234")
```
"""


def resolve_parent_forward_arg(annotation: Any) -> Any:
    if isinstance(annotation, str):
        str_annotation = annotation
    elif isinstance(annotation, ForwardRef):
        str_annotation = annotation.__forward_arg__
    else:
        # If neither, return the annotation as is
        return annotation

    if parent_match := _parent_re.match(str_annotation):
        annotation = Parent[ForwardRef(parent_match.group(1))]  # type: ignore[misc]

    return annotation


__all__ = ["Parent", "StrawberryParent", "resolve_parent_forward_arg"]
