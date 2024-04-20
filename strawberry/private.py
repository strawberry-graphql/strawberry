from typing import TypeVar
from typing_extensions import Annotated

from strawberry.utils.typing import type_has_annotation


class StrawberryPrivate: ...


T = TypeVar("T")

Private = Annotated[T, StrawberryPrivate()]
Private.__doc__ = """Represents a field that won't be exposed in the GraphQL schema

Example:

>>> import strawberry
>>> @strawberry.type
... class User:
...     name: str
...     age: strawberry.Private[int]
"""


def is_private(type_: object) -> bool:
    return type_has_annotation(type_, StrawberryPrivate)
