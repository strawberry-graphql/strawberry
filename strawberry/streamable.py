from typing import AsyncGenerator, TypeVar
from typing_extensions import Annotated

from strawberry.utils.typing import type_has_annotation


class StrawberryStreamable:
    ...


T = TypeVar("T")

Streamable = Annotated[AsyncGenerator[T, None], StrawberryStreamable()]
Streamable.__doc__ = """Represents a field that can be streamed.
The GraphQL schema will be a list of the type, and the client will be able
to use the @stream directive to receive updates as they come.

Example:

>>> import strawberry
>>> @strawberry.type
... class User:
...     name: str
...     posts: strawberry.Streamable[Post]
"""


def is_streamable(type_: object) -> bool:
    return type_has_annotation(type_, StrawberryStreamable)
