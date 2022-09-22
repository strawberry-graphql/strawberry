from typing import Iterable, Optional, Sequence, Type, Union

from strawberry.union import union as base_union


def union(
    name: str,
    types: Sequence[Type],
    *,
    description: str = None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
) -> Union[Type]:
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
