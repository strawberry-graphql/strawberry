from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    overload,
)

from strawberry.types.field import field as base_field
from strawberry.types.unset import UNSET

from .types import FieldSet

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from typing import Literal

    from strawberry.extensions.field_extension import FieldExtension
    from strawberry.permission import BasePermission
    from strawberry.types.field import (
        _RESOLVER_TYPE,
        _RESOLVER_TYPE_ASYNC,
        _RESOLVER_TYPE_SYNC,
        StrawberryField,
    )

    from .schema_directives import Override

T = TypeVar("T")

# NOTE: we are separating the sync and async resolvers because using both
# in the same function will cause mypy to raise an error. Not sure if it is a bug


@overload
def field(
    *,
    resolver: _RESOLVER_TYPE_ASYNC[T],
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    provides: list[str] | None = None,
    override: Override | str | None = None,
    requires: list[str] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
    shareable: bool = False,
    init: Literal[False] = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> T: ...


@overload
def field(
    *,
    resolver: _RESOLVER_TYPE_SYNC[T],
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    provides: list[str] | None = None,
    override: Override | str | None = None,
    requires: list[str] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
    shareable: bool = False,
    init: Literal[False] = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> T: ...


@overload
def field(
    *,
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    provides: list[str] | None = None,
    override: Override | str | None = None,
    requires: list[str] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
    shareable: bool = False,
    init: Literal[True] = True,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> Any: ...


@overload
def field(
    resolver: _RESOLVER_TYPE_ASYNC[T],
    *,
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    provides: list[str] | None = None,
    override: Override | str | None = None,
    requires: list[str] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
    shareable: bool = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> StrawberryField: ...


@overload
def field(
    resolver: _RESOLVER_TYPE_SYNC[T],
    *,
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    provides: list[str] | None = None,
    override: Override | str | None = None,
    requires: list[str] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
    shareable: bool = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> StrawberryField: ...


def field(
    resolver: _RESOLVER_TYPE[Any] | None = None,
    *,
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: list[list[str]] | None = None,
    provides: list[str] | None = None,
    override: Override | str | None = None,
    requires: list[str] | None = None,
    requires_scopes: list[list[str]] | None = None,
    tags: Iterable[str] | None = (),
    shareable: bool = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False] | None = None,
) -> Any:
    from .schema_directives import (
        Authenticated,
        External,
        Inaccessible,
        Override,
        Policy,
        Provides,
        Requires,
        RequiresScopes,
        Shareable,
        Tag,
    )

    directives = list(directives or [])

    if authenticated:
        directives.append(Authenticated())

    if external:
        directives.append(External())

    if inaccessible:
        directives.append(Inaccessible())

    if override:
        directives.append(
            Override(override_from=override, label=UNSET)
            if isinstance(override, str)
            else override
        )

    if policy:
        directives.append(Policy(policies=policy))

    if provides:
        directives.append(Provides(fields=FieldSet(" ".join(provides))))

    if requires:
        directives.append(Requires(fields=FieldSet(" ".join(requires))))

    if requires_scopes:
        directives.append(RequiresScopes(scopes=requires_scopes))

    if shareable:
        directives.append(Shareable())

    if tags:
        directives.extend(Tag(name=tag) for tag in tags)

    return base_field(  # type: ignore
        resolver=resolver,  # type: ignore
        name=name,
        is_subscription=is_subscription,
        description=description,
        permission_classes=permission_classes,
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        init=init,  # type: ignore
        directives=directives,
        metadata=metadata,
        extensions=extensions,
        graphql_type=graphql_type,
    )


__all__ = ["field"]
