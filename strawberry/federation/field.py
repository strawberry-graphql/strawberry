from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    overload,
)
from typing_extensions import Unpack

from strawberry.types.field import field as base_field

from .params import FederationFieldParams, process_federation_field_directives

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from typing import Literal

    from strawberry.extensions.field_extension import FieldExtension
    from strawberry.permission import BasePermission
    from strawberry.types.field import (
        _RESOLVER_TYPE,
        _RESOLVER_TYPE_ASYNC,
        _RESOLVER_TYPE_SYNC,
    )

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
    init: Literal[False] = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
    **federation_kwargs: Unpack[FederationFieldParams],
) -> T: ...


@overload
def field(
    *,
    resolver: _RESOLVER_TYPE_SYNC[T],
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
    init: Literal[False] = False,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
    **federation_kwargs: Unpack[FederationFieldParams],
) -> T: ...


@overload
def field(
    *,
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
    init: Literal[True] = True,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    default: Any = dataclasses.MISSING,
    default_factory: Callable[..., object] | object = dataclasses.MISSING,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
    **federation_kwargs: Unpack[FederationFieldParams],
) -> Any: ...


def field(
    resolver: _RESOLVER_TYPE[Any] | None = None,
    *,
    name: str | None = None,
    is_subscription: bool = False,
    description: str | None = None,
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
    **federation_kwargs: Unpack[FederationFieldParams],
) -> Any:
    directives = process_federation_field_directives(directives, **federation_kwargs)

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
