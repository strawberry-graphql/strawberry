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
        raise ValueError("Cannot use union type directly")


def union(
    name: str, types: Tuple[Type, ...], *, description: str = None
) -> StrawberryUnion:
    """Creates a new named Union type.

    Example usages:

    >>> strawberry.union(
    ...      "Name",
    ...      (A, B),
    ... )

    >>> strawberry.union(
    ...     "Name",
    ...     (A, B),
    ... )
    """

    union_definition = StrawberryUnion(name=name, types=types, description=description)

    return union_definition
