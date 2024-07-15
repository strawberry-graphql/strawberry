from typing import Any, Collection, Iterable, Optional, Type

from strawberry.types.union import StrawberryUnion
from strawberry.types.union import union as base_union


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

    Args:
        name: The GraphQL name of the Union type.
        types: The types that the Union can be.
            (Deprecated, use `Annotated[U, strawberry.federation.union("Name")]` instead)
        description: The  GraphQL description of the Union type.
        directives: The directives to attach to the Union type.
        inaccessible: Whether the Union type is inaccessible.
        tags: The federation tags to attach to the Union type.

    Example usages:

    ```python
    import strawberry
    from typing import Annotated

    @strawberry.federation.type(keys=["id"])
    class A:
        id: strawberry.ID

    @strawberry.federation.type(keys=["id"])
    class B:
        id: strawberry.ID

    MyUnion = Annotated[A | B, strawberry.federation.union("Name", tags=["tag"])]
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


__all__ = ["union"]
