from typing import TypeVar
from typing_extensions import Annotated


class StrawberryParent: ...


T = TypeVar("T")

Parent = Annotated[T, StrawberryParent()]
Parent.__doc__ = """Represents a parameter holding the parent resolver's value.

This can be used when defining a resolver on a type when the parent isn't expected
to return the type itself.

Example:

>>> import strawberry
>>> from dataclasses import dataclass
>>>
>>> @dataclass
>>> class UserRow:
...     id_: str
...
>>> @strawberry.type
... class User:
...     @strawberry.field
...     @staticmethod
...     async def name(parent: strawberry.Parent[UserRow]) -> str:
...         return f"User Number {parent.id}"
...
>>> @strawberry.type
>>> class Query:
...     @strawberry.field
...     def user(self) -> User:
...         return UserRow(id_="1234")
...
"""
