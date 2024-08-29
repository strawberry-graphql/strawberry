from typing import (
    TYPE_CHECKING,
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
from typing_extensions import dataclass_transform

from strawberry.types.field import StrawberryField
from strawberry.types.field import field as base_field
from strawberry.types.object_type import type as base_type
from strawberry.types.unset import UNSET

from .field import field

if TYPE_CHECKING:
    from .schema_directives import Key


T = TypeVar("T", bound=Type)


def _impl_type(
    cls: Optional[T],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    one_of: Optional[bool] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    keys: Iterable[Union["Key", str]] = (),
    extend: bool = False,
    shareable: bool = False,
    inaccessible: bool = UNSET,
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Iterable[str] = (),
    is_input: bool = False,
    is_interface: bool = False,
    is_interface_object: bool = False,
) -> T:
    from strawberry.federation.schema_directives import (
        Authenticated,
        Inaccessible,
        InterfaceObject,
        Key,
        Policy,
        RequiresScopes,
        Shareable,
        Tag,
    )
    from strawberry.schema_directives import OneOf

    directives = list(directives)

    directives.extend(
        Key(fields=key, resolvable=UNSET) if isinstance(key, str) else key
        for key in keys
    )

    if authenticated:
        directives.append(Authenticated())

    if inaccessible is not UNSET:
        directives.append(Inaccessible())

    if policy:
        directives.append(Policy(policies=policy))

    if requires_scopes:
        directives.append(RequiresScopes(scopes=requires_scopes))

    if shareable:
        directives.append(Shareable())

    if tags:
        directives.extend(Tag(name=tag) for tag in tags)

    if is_interface_object:
        directives.append(InterfaceObject())

    if one_of:
        directives.append(OneOf())

    return base_type(  # type: ignore
        cls,
        name=name,
        description=description,
        directives=directives,
        extend=extend,
        is_input=is_input,
        is_interface=is_interface,
    )


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def type(
    cls: T,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    extend: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    shareable: bool = False,
    tags: Iterable[str] = (),
) -> T: ...


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def type(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    extend: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    shareable: bool = False,
    tags: Iterable[str] = (),
) -> Callable[[T], T]: ...


def type(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    extend: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    shareable: bool = False,
    tags: Iterable[str] = (),
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        authenticated=authenticated,
        keys=keys,
        extend=extend,
        inaccessible=inaccessible,
        policy=policy,
        requires_scopes=requires_scopes,
        shareable=shareable,
        tags=tags,
    )


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def input(
    cls: T,
    *,
    name: Optional[str] = None,
    one_of: Optional[bool] = None,
    description: Optional[str] = None,
    directives: Sequence[object] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
) -> T: ...


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def input(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    one_of: Optional[bool] = None,
    directives: Sequence[object] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
) -> Callable[[T], T]: ...


def input(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    one_of: Optional[bool] = None,
    description: Optional[str] = None,
    directives: Sequence[object] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        inaccessible=inaccessible,
        is_input=True,
        one_of=one_of,
        tags=tags,
    )


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def interface(
    cls: T,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Iterable[str] = (),
) -> T: ...


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def interface(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Iterable[str] = (),
) -> Callable[[T], T]: ...


def interface(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Iterable[str] = (),
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        authenticated=authenticated,
        keys=keys,
        inaccessible=inaccessible,
        policy=policy,
        requires_scopes=requires_scopes,
        tags=tags,
        is_interface=True,
    )


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def interface_object(
    cls: T,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Iterable[str] = (),
) -> T: ...


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def interface_object(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Iterable[str] = (),
) -> Callable[[T], T]: ...


def interface_object(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Iterable[str] = (),
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        authenticated=authenticated,
        keys=keys,
        inaccessible=inaccessible,
        policy=policy,
        requires_scopes=requires_scopes,
        tags=tags,
        is_interface=False,
        is_interface_object=True,
    )


__all__ = ["type", "input", "interface", "interface_object"]
