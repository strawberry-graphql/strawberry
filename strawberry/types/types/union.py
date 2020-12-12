from typing import NoReturn, Optional, Tuple

from .type import StrawberryType


class StrawberryUnion(StrawberryType):
    def __init__(
        self, name: str, types: Tuple[StrawberryType, ...],
        description: Optional[str] = None
    ):
        super().__init__(name=name, description=description)
        self.children = types

    def __call__(self, *_args, **_kwargs) -> NoReturn:
        """Do not use.

        Used to bypass
        https://github.com/python/cpython/blob/5efb1a77e75648012f8b52960c8637fc296a5c6d/Lib/typing.py#L148-L149
        """
        raise ValueError("Cannot use union type directly")


def union(
    name: str, types: Tuple[StrawberryType, ...], *, description: str = None
) -> StrawberryUnion:
    """Creates a new named Union type.

    Example usages:

    >>> strawberry.union("Some Thing", (int, str))

    >>> @strawberry.type
    ... class A: ...
    >>> @strawberry.type
    ... class B: ...
    >>> strawberry.union("Name", (A, Optional[B]))
    """

    union_definition = StrawberryUnion(
        name=name,
        types=types,
        description=description
    )

    return union_definition
