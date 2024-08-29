from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    overload,
)

from strawberry.types.field import field as base_field
from strawberry.types.unset import UNSET

if TYPE_CHECKING:
    from typing_extensions import Literal

    from strawberry.extensions.field_extension import FieldExtension
    from strawberry.permission import BasePermission
    from strawberry.types.field import _RESOLVER_TYPE, StrawberryField

    from .schema_directives import Override

T = TypeVar("T")


@overload
def field(
    *,
    resolver: _RESOLVER_TYPE[T],
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: Optional[List[List[str]]] = None,
    provides: Optional[List[str]] = None,
    override: Optional[Union[Override, str]] = None,
    requires: Optional[List[str]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Optional[Iterable[str]] = (),
    shareable: bool = False,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable[..., object], object] = UNSET,
    directives: Sequence[object] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> T: ...


@overload
def field(
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: Optional[List[List[str]]] = None,
    provides: Optional[List[str]] = None,
    override: Optional[Union[Override, str]] = None,
    requires: Optional[List[str]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Optional[Iterable[str]] = (),
    shareable: bool = False,
    init: Literal[True] = True,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable[..., object], object] = UNSET,
    directives: Sequence[object] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> Any: ...


@overload
def field(
    resolver: _RESOLVER_TYPE[T],
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: Optional[List[List[str]]] = None,
    provides: Optional[List[str]] = None,
    override: Optional[Union[Override, str]] = None,
    requires: Optional[List[str]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Optional[Iterable[str]] = (),
    shareable: bool = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable[..., object], object] = UNSET,
    directives: Sequence[object] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> StrawberryField: ...


def field(
    resolver: Optional[_RESOLVER_TYPE[Any]] = None,
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    authenticated: bool = False,
    external: bool = False,
    inaccessible: bool = False,
    policy: Optional[List[List[str]]] = None,
    provides: Optional[List[str]] = None,
    override: Optional[Union[Override, str]] = None,
    requires: Optional[List[str]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Optional[Iterable[str]] = (),
    shareable: bool = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    directives: Sequence[object] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False, None] = None,
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

    directives = list(directives)

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
        directives.append(Provides(fields=" ".join(provides)))

    if requires:
        directives.append(Requires(fields=" ".join(requires)))

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
        extensions=extensions,
        graphql_type=graphql_type,
    )


__all__ = ["field"]
