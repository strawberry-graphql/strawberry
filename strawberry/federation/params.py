"""Shared TypedDicts and processing functions for federation directives.

Provides ``FederationFieldParams``, ``FederationInterfaceParams``, and
``FederationTypeParams`` TypedDicts that can be consumed via
``Unpack[...]`` to avoid duplicating federation parameter lists.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing_extensions import TypedDict

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from .schema_directives import Key, Override


class FederationFieldParams(TypedDict, total=False):
    """Federation parameters accepted by field decorators."""

    authenticated: bool
    external: bool
    inaccessible: bool
    policy: Sequence[Sequence[str]]
    provides: Sequence[str]
    override: Override | str
    requires: Sequence[str]
    requires_scopes: Sequence[Sequence[str]]
    shareable: bool
    tags: Sequence[str]


class FederationInterfaceParams(TypedDict, total=False):
    """Federation parameters accepted by interface decorators."""

    keys: Sequence[Key | str]
    authenticated: bool
    inaccessible: bool
    policy: Sequence[Sequence[str]]
    requires_scopes: Sequence[Sequence[str]]
    tags: Sequence[str]


class FederationTypeParams(FederationInterfaceParams, total=False):
    """Federation parameters accepted by type decorators.

    Extends :class:`FederationInterfaceParams` with ``extend`` and ``shareable``.
    """

    extend: bool
    shareable: bool


def process_federation_field_directives(
    directives: Sequence[object] | None,
    *,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: Sequence[Sequence[str]] | None = None,
    provides: Sequence[str] | None = None,
    override: Override | str | None = None,
    requires: Sequence[str] | None = None,
    requires_scopes: Sequence[Sequence[str]] | None = None,
    shareable: bool = False,
    tags: Iterable[str] | None = None,
) -> list[object]:
    """Convert federation field parameters into directive instances.

    Returns a new list starting with *directives*, extended with any
    directive objects implied by the keyword arguments.
    """
    from strawberry.types.unset import UNSET

    from .schema_directives import (
        Authenticated,
        External,
        Inaccessible,
        Policy,
        Provides,
        Requires,
        RequiresScopes,
        Shareable,
        Tag,
    )
    from .schema_directives import (
        Override as OverrideDirective,
    )
    from .types import FieldSet

    result = list(directives or [])

    if authenticated:
        result.append(Authenticated())

    if external:
        result.append(External())

    if inaccessible:
        result.append(Inaccessible())

    if override:
        result.append(
            OverrideDirective(override_from=override, label=UNSET)
            if isinstance(override, str)
            else override
        )

    if policy:
        result.append(Policy(policies=[list(p) for p in policy]))

    if provides:
        result.append(Provides(fields=FieldSet(" ".join(provides))))

    if requires:
        result.append(Requires(fields=FieldSet(" ".join(requires))))

    if requires_scopes:
        result.append(RequiresScopes(scopes=[list(s) for s in requires_scopes]))

    if shareable:
        result.append(Shareable())

    if tags:
        result.extend(Tag(name=tag) for tag in tags)

    return result


def process_federation_type_directives(
    directives: Iterable[object] | None,
    *,
    keys: Iterable[Key | str] = (),
    extend: bool = False,
    shareable: bool = False,
    inaccessible: bool = False,
    authenticated: bool = False,
    policy: Sequence[Sequence[str]] | None = None,
    requires_scopes: Sequence[Sequence[str]] | None = None,
    tags: Iterable[str] = (),
) -> tuple[list[object], bool]:
    """Convert federation type/interface parameters into directive instances.

    Returns ``(directives, extend)`` where *directives* is a new list
    starting with the input directives, extended with any directive objects
    implied by the keyword arguments.
    """
    from strawberry.types.unset import UNSET

    from .schema_directives import (
        Authenticated,
        Inaccessible,
        Policy,
        RequiresScopes,
        Shareable,
        Tag,
    )
    from .schema_directives import (
        Key as KeyDirective,
    )
    from .types import FieldSet

    result = list(directives or [])

    result.extend(
        KeyDirective(fields=FieldSet(key), resolvable=UNSET)
        if isinstance(key, str)
        else key
        for key in keys
    )

    if authenticated:
        result.append(Authenticated())

    if inaccessible:
        result.append(Inaccessible())

    if policy:
        result.append(Policy(policies=[list(p) for p in policy]))

    if requires_scopes:
        result.append(RequiresScopes(scopes=[list(s) for s in requires_scopes]))

    if shareable:
        result.append(Shareable())

    if tags:
        result.extend(Tag(name=tag) for tag in tags)

    return result, extend


__all__ = [
    "FederationFieldParams",
    "FederationInterfaceParams",
    "FederationTypeParams",
    "process_federation_field_directives",
    "process_federation_type_directives",
]
