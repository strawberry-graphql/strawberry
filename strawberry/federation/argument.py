from typing import Iterable, Optional

from strawberry.arguments import StrawberryArgumentAnnotation
from strawberry.description_sources import DescriptionSources


def argument(
    description_sources: Optional[DescriptionSources] = None,
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
        description_sources=description_sources,
        description=description,
        name=name,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )
