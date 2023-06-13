from typing import (
    TYPE_CHECKING,
    Callable,
    Iterable,
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

if TYPE_CHECKING:
    from .schema_directives import Key


T = TypeVar("T", bound=Type)


def _impl_type(
    cls: Optional[T],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
    keys: Iterable[Union["Key", str]] = (),
    extend: bool = False,
    shareable: bool = False,
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    is_input: bool = False,
    is_interface: bool = False,
    is_interface_object: bool = False,
) -> T:
    from strawberry.federation.schema_directives import (
        Inaccessible,
        InterfaceObject,
        Key,
        Shareable,
        Tag,
    )

    directives = list(directives)

    directives.extend(
        Key(fields=key, resolvable=UNSET) if isinstance(key, str) else key
        for key in keys
    )

    if shareable:
        directives.append(Shareable())

    if inaccessible is not UNSET:
        directives.append(Inaccessible())

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
    keys: Iterable[Union["Key", str]] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    extend: bool = False,
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
    keys: Iterable[Union["Key", str]] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    extend: bool = False,
    shareable: bool = False,
    directives: Iterable[object] = (),
) -> Callable[[T], T]:
    ...


def type(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    keys: Iterable[Union["Key", str]] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    extend: bool = False,
    shareable: bool = False,
    directives: Iterable[object] = (),
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        keys=keys,
        extend=extend,
        shareable=shareable,
        inaccessible=inaccessible,
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
    keys: Iterable[Union["Key", str]] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    directives: Iterable[object] = (),
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
    keys: Iterable[Union["Key", str]] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    directives: Iterable[object] = (),
) -> Callable[[T], T]:
    ...


def interface(
    cls: Optional[T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    keys: Iterable[Union["Key", str]] = (),
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    directives: Iterable[object] = (),
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        keys=keys,
        inaccessible=inaccessible,
        is_interface=True,
        tags=tags,
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
    keys: Iterable[Union["Key", str]],
    name: Optional[str] = None,
    description: Optional[str] = None,
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    directives: Iterable[object] = (),
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
    keys: Iterable[Union["Key", str]],
    name: Optional[str] = None,
    description: Optional[str] = None,
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    directives: Iterable[object] = (),
) -> Callable[[T], T]:
    ...


def interface_object(
    cls: Optional[T] = None,
    *,
    keys: Iterable[Union["Key", str]],
    name: Optional[str] = None,
    description: Optional[str] = None,
    inaccessible: bool = UNSET,
    tags: Iterable[str] = (),
    directives: Iterable[object] = (),
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        keys=keys,
        inaccessible=inaccessible,
        is_interface=False,
        is_interface_object=True,
        tags=tags,
    )
