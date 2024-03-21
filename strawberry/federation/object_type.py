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

from strawberry.field import StrawberryField
from strawberry.field import field as base_field
from strawberry.object_type import type as base_type
from strawberry.unset import UNSET

from .field import field
from .types import Federation__Policy, Federation__Scope

if TYPE_CHECKING:
    from .schema_directives import Key


T = TypeVar("T", bound=Type)


def _impl_type(
    cls: Optional[T],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    extend: bool = False,
    shareable: bool = False,
    inaccessible: bool = UNSET,
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
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

    directives = list(directives)

    directives.extend(
        Key(fields=key, resolvable=UNSET) if isinstance(key, str) else key
        for key in keys
    )

    if authenticated is not UNSET:
        directives.append(Authenticated())

    if inaccessible is not UNSET:
        directives.append(Inaccessible())

    if policies:
        directives.append(Policy(policies=policies))

    if requires_scopes:
        directives.append(RequiresScopes(scopes=requires_scopes))

    if shareable:
        directives.append(Shareable())

    if tags:
        directives.extend(Tag(name=tag) for tag in tags)

    if is_interface_object:
        directives.append(InterfaceObject())

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
    authenticated: bool = UNSET,
    extend: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
    shareable: bool = False,
    tags: Iterable[str] = (),
) -> T:
    ...


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
    authenticated: bool = UNSET,
    extend: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
    shareable: bool = False,
    tags: Iterable[str] = (),
) -> Callable[[T], T]:
    ...


def type(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = UNSET,
    extend: bool = False,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
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
        policies=policies,
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
    description: Optional[str] = None,
    directives: Sequence[object] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
) -> T:
    ...


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
    directives: Sequence[object] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
) -> Callable[[T], T]:
    ...


def input(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
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
    authenticated: bool = UNSET,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
    tags: Iterable[str] = (),
) -> T:
    ...


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
    authenticated: bool = UNSET,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
    tags: Iterable[str] = (),
) -> Callable[[T], T]:
    ...


def interface(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = UNSET,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
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
        policies=policies,
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
    authenticated: bool = UNSET,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
    tags: Iterable[str] = (),
) -> T:
    ...


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
    authenticated: bool = UNSET,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
    tags: Iterable[str] = (),
) -> Callable[[T], T]:
    ...


def interface_object(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    authenticated: bool = UNSET,
    inaccessible: bool = UNSET,
    keys: Iterable[Union["Key", str]] = (),
    policies: Optional[List[List[Federation__Policy]]] = None,
    requires_scopes: Optional[List[List[Federation__Scope]]] = None,
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
        policies=policies,
        requires_scopes=requires_scopes,
        tags=tags,
        is_interface=False,
        is_interface_object=True,
    )
