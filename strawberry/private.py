from typing import TypeVar, Union

from typing_extensions import Annotated

from strawberry.type import StrawberryAnnotated, StrawberryType


class StrawberryPrivate:
    ...


T = TypeVar("T")

Private = Annotated[T, StrawberryPrivate()]
Private.__doc__ = """Represent a private field that won't be converted into a GraphQL field

Example:

>>> import strawberry
>>> @strawberry.type
... class User:
...     name: str
...     age: strawberry.Private[int]
"""


def is_private(type: Union[StrawberryType, type]) -> bool:
    type, args = StrawberryAnnotated.get_type_and_args(type)
    return any(isinstance(argument, StrawberryPrivate) for argument in args)
