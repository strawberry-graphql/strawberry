from typing import Callable, Iterable, Optional, Union, overload

from strawberry.enum import EnumType, _process_enum


@overload
def enum(
    _cls: EnumType,
    *,
    name=None,
    description=None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
) -> EnumType:
    ...


@overload
def enum(
    _cls: None = None,
    *,
    name=None,
    description=None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
) -> Callable[[EnumType], EnumType]:
    ...


def enum(
    _cls: Optional[EnumType] = None,
    *,
    name=None,
    description=None,
    directives=(),
    inaccessible=False,
    tags=(),
) -> Union[EnumType, Callable[[EnumType], EnumType]]:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    from strawberry.federation.schema_directives import Inaccessible, Tag

    directives = list(directives)

    if inaccessible:
        directives.append(Inaccessible())

    if tags:
        directives.extend(Tag(tag) for tag in tags)

    def wrap(cls: EnumType) -> EnumType:
        return _process_enum(cls, name, description, directives=directives)

    if not _cls:
        return wrap

    return wrap(_cls)
