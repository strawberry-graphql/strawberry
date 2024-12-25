from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    overload,
)

from strawberry.types.enum import _process_enum
from strawberry.types.enum import enum_value as base_enum_value

if TYPE_CHECKING:
    from collections.abc import Iterable

    from strawberry.enum import EnumType, EnumValueDefinition


def enum_value(
    value: Any,
    deprecation_reason: str | None = None,
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
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
) -> EnumType: ...


@overload
def enum(
    _cls: None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
) -> Callable[[EnumType], EnumType]: ...


def enum(
    _cls: EnumType | None = None,
    *,
    name=None,
    description=None,
    directives=(),
    authenticated: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
) -> EnumType | Callable[[EnumType], EnumType]:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """
    from strawberry.federation.schema_directives import (
        Authenticated,
        Inaccessible,
        Policy,
        RequiresScopes,
        Tag,
    )

    directives = list(directives)

    if authenticated:
        directives.append(Authenticated())

    if inaccessible:
        directives.append(Inaccessible())

    if policy:
        directives.append(Policy(policies=policy))

    if requires_scopes:
        directives.append(RequiresScopes(scopes=requires_scopes))

    if tags:
        directives.extend(Tag(name=tag) for tag in tags)

    def wrap(cls: EnumType) -> EnumType:
        return _process_enum(cls, name, description, directives=directives)

    if not _cls:
        return wrap

    return wrap(_cls)  # pragma: no cover


__all__ = ["enum", "enum_value"]
