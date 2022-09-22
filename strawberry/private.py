from typing import TypeVar

from typing_extensions import Annotated, get_args, get_origin


class StrawberryPrivate:
    ...


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
    if get_origin(type_) is Annotated:
        return any(
            isinstance(argument, StrawberryPrivate) for argument in get_args(type_)
        )

    return False
