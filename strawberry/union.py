from typing import NoReturn, Optional, Tuple, Type


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

    >>> strawberry.union("Some Thing", (int, str))

    >>> @strawberry.type
    ... class A: ...
    >>> @strawberry.type
    ... class B: ...
    >>> strawberry.union("Name", (A, Optional[B]))
    """

    union_definition = StrawberryUnion(name=name, types=types, description=description)

    return union_definition
