from typing import Any, Collection, Iterable, Optional, Type

from strawberry.union import StrawberryUnion
from strawberry.union import union as base_union


def union(
    name: str,
    types: Optional[Collection[Type[Any]]] = None,
    *,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
) -> StrawberryUnion:
    """Creates a new named Union type.

    Example usages:

    >>> @strawberry.type
    ... class A: ...
    >>> @strawberry.type
    ... class B: ...
    >>> strawberry.federation.union("Name", (A, Optional[B]))
    """

    from strawberry.federation.schema_directives import Inaccessible, Tag

    directives = list(directives)

    if inaccessible:
        directives.append(Inaccessible())

    if tags:
        directives.extend(Tag(name=tag) for tag in tags)

    return base_union(
        name,
        types,
        description=description,
        directives=directives,
    )
