from typing import (
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

from typing_extensions import Literal

from strawberry.field import _RESOLVER_TYPE, StrawberryField, field as base_field
from strawberry.permission import BasePermission
from strawberry.unset import UNSET


T = TypeVar("T")


@overload
def field(
    *,
    resolver: Callable[[], T],
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    provides: Optional[List[str]] = None,
    requires: Optional[List[str]] = None,
    external: bool = False,
    shareable: bool = False,
    tags: Optional[Iterable[str]] = (),
    override: Optional[str] = None,
    inaccessible: bool = False,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
    directives: Sequence[object] = (),
) -> T:
    ...


@overload
def field(
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    provides: Optional[List[str]] = None,
    requires: Optional[List[str]] = None,
    external: bool = False,
    shareable: bool = False,
    tags: Optional[Iterable[str]] = (),
    override: Optional[str] = None,
    inaccessible: bool = False,
    init: Literal[True] = True,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
    directives: Sequence[object] = (),
) -> Any:
    ...


@overload
def field(
    resolver: _RESOLVER_TYPE,
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    provides: Optional[List[str]] = None,
    requires: Optional[List[str]] = None,
    external: bool = False,
    shareable: bool = False,
    tags: Optional[Iterable[str]] = (),
    override: Optional[str] = None,
    inaccessible: bool = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
    directives: Sequence[object] = (),
) -> StrawberryField:
    ...


def field(
    resolver=None,
    *,
    name=None,
    is_subscription=False,
    description=None,
    provides=None,
    requires=None,
    external=False,
    shareable=False,
    tags=None,
    override=None,
    inaccessible=False,
    permission_classes=None,
    deprecation_reason=None,
    default=UNSET,
    default_factory=UNSET,
    directives: Sequence[object] = (),
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init=None,
) -> Any:
    from .schema_directives import (
        External,
        Inaccessible,
        Override,
        Provides,
        Requires,
        Shareable,
        Tag,
    )

    directives = list(directives)

    if provides:
        directives.append(Provides(" ".join(provides)))

    if requires:
        directives.append(Requires(" ".join(requires)))

    if external:
        directives.append(External())

    if shareable:
        directives.append(Shareable())

    if tags:
        directives.append(Tag(" ".join(tags)))

    if override:
        directives.append(Override(override))

    if inaccessible:
        directives.append(Inaccessible())

    return base_field(
        resolver=resolver,
        name=name,
        is_subscription=is_subscription,
        description=description,
        permission_classes=permission_classes,
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        init=init,
        directives=directives,
    )
