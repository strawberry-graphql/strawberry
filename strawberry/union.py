from typing import NoReturn, Optional, Tuple, Type, TypeVar

from .exceptions import InvalidUnionType
from .scalars import SCALAR_TYPES


class StrawberryUnion:
    def __init__(
        self, name: str, types: Tuple[Type, ...], description: Optional[str] = None
    ):
        self.name = name
        self._types = types
        self.description = description

    @property
    def types(self) -> Tuple[Type, ...]:
        from .types.type_resolver import _resolve_generic_type

        types = tuple(
            _resolve_generic_type(t, self.name)
            for t in self._types
            if t is not None.__class__
        )

        return types

    def __call__(self, *_args, **_kwargs) -> NoReturn:
        """Do not use.

        Used to bypass
        https://github.com/python/cpython/blob/5efb1a77e75648012f8b52960c8637fc296a5c6d/Lib/typing.py#L148-L149
        """
        raise ValueError("Cannot use union type directly")


def union(
    name: str, types: Tuple[Type, ...], *, description: str = None
) -> StrawberryUnion:
    """Creates a new named Union type.

    Example usages:

    >>> @strawberry.type
    ... class A: ...
    >>> @strawberry.type
    ... class B: ...
    >>> strawberry.union("Name", (A, Optional[B]))
    """

    # Validate types
    if len(types) == 0:
        raise TypeError("No types passed to `union`")

    for _type in types:
        if _type in SCALAR_TYPES:
            raise InvalidUnionType(
                f"Scalar type `{_type.__name__}` cannot be used in a GraphQL Union"
            )

        if not isinstance(_type, TypeVar) and not hasattr(_type, "_type_definition"):
            raise InvalidUnionType(
                f"Union type `{_type.__name__}` is not a Strawberry type"
            )

    union_definition = StrawberryUnion(name=name, types=types, description=description)

    return union_definition
