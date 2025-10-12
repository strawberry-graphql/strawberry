from collections.abc import Iterable

from strawberry.types.arguments import StrawberryArgumentAnnotation


def argument(
    description: str | None = None,
    name: str | None = None,
    deprecation_reason: str | None = None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Iterable[str] | None = (),
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
