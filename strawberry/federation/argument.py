from typing import Iterable, Optional

from strawberry.types.arguments import StrawberryArgumentAnnotation


def argument(
    description: Optional[str] = None,
    name: Optional[str] = None,
    deprecation_reason: Optional[str] = None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
) -> StrawberryArgumentAnnotation:
    from strawberry.federation.schema_directives import Inaccessible, Tag

    directives = list(directives)

    if inaccessible:
        directives.append(Inaccessible())

    if tags:
        directives.extend(Tag(name=tag) for tag in tags)

    return StrawberryArgumentAnnotation(
        description=description,
        name=name,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )


__all__ = ["argument"]
