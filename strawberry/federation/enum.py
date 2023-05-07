from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional, Union, overload

from strawberry.enum import _process_enum
from strawberry.enum import enum_value as base_enum_value

if TYPE_CHECKING:
    from strawberry.enum import EnumType, EnumValueDefinition


def enum_value(
    value: Any,
    deprecation_reason: Optional[str] = None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Iterable[str] = (),
) -> EnumValueDefinition:
    from strawberry.federation.schema_directives import Inaccessible, Tag

    directives = list(directives)

    if inaccessible:
        directives.append(Inaccessible())

    if tags:
        directives.extend(Tag(name=tag) for tag in tags)

    return base_enum_value(value, deprecation_reason, directives)


@overload
def enum(
    _cls: EnumType,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
) -> EnumType:
    ...


@overload
def enum(
    _cls: None = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
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
        directives.extend(Tag(name=tag) for tag in tags)

    def wrap(cls: EnumType) -> EnumType:
        return _process_enum(cls, name, description, directives=directives)

    if not _cls:
        return wrap

    return wrap(_cls)  # pragma: no cover
