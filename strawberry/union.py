import typing
from dataclasses import dataclass


@dataclass
class UnionDefinition:
    name: str
    description: typing.Optional[str]
    types: typing.Tuple[typing.Type]


def union(name: str, types: typing.Tuple[typing.Type], *, description=None):
    """Creates a new named Union type.

    Example usages:

    >>> strawberry.union(
    >>>     "Name",
    >>>     (A, B),
    >>> )

    >>> strawberry.union(
    >>>     "Name",
    >>>     (A, B),
    >>> )
    """

    union_definition = UnionDefinition(name=name, description=description, types=types)

    # This is currently a temporary solution, this is ok for now
    # But in future we might want to change this so that it works
    # properly with mypy, but there's no way to return a type like NewType does
    # so we return this class instance as it allows us to reuse the rest of
    # our code without doing too many changes

    def _call(self):
        raise ValueError("Cannot use union type directly")

    union_class = type(
        name, (), {"_union_definition": union_definition, "__call__": _call},
    )

    return union_class()
