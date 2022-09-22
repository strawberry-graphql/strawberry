from typing import Iterable, Optional, Tuple, Type, TypeVar, Union

from strawberry.union import union as base_union


Types = TypeVar("Types", bound=Type)


def union(
    name: str,
    types: Tuple[Types, ...],
    *,
    description: str = None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
) -> Union[Types]:
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
