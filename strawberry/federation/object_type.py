import builtins
from collections.abc import Callable, Iterable, Sequence
from typing import (
    TypeVar,
    overload,
)
from typing_extensions import Unpack, dataclass_transform

from strawberry.types.field import StrawberryField
from strawberry.types.field import field as base_field
from strawberry.types.object_type import type as base_type

from .field import field
from .params import (
    FederationInterfaceParams,
    FederationTypeParams,
    process_federation_type_directives,
)

T = TypeVar("T", bound=builtins.type)


def _impl_type(
    cls: T | None,
    *,
    name: str | None = None,
    description: str | None = None,
    one_of: bool | None = None,
    directives: Iterable[object] = (),
    is_input: bool = False,
    is_interface: bool = False,
    is_interface_object: bool = False,
    **federation_kwargs: Unpack[FederationTypeParams],
) -> T:
    from strawberry.federation.schema_directives import InterfaceObject
    from strawberry.schema_directives import OneOf

    directives, extend = process_federation_type_directives(
        directives, **federation_kwargs
    )

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
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    **federation_kwargs: Unpack[FederationTypeParams],
) -> T: ...


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def type(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    **federation_kwargs: Unpack[FederationTypeParams],
) -> Callable[[T], T]: ...


def type(
    cls: T | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    **federation_kwargs: Unpack[FederationTypeParams],
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        **federation_kwargs,
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
    name: str | None = None,
    one_of: bool | None = None,
    description: str | None = None,
    directives: Sequence[object] = (),
    inaccessible: bool = False,
    tags: Sequence[str] = (),
) -> T: ...


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def input(
    *,
    name: str | None = None,
    description: str | None = None,
    one_of: bool | None = None,
    directives: Sequence[object] = (),
    inaccessible: bool = False,
    tags: Sequence[str] = (),
) -> Callable[[T], T]: ...


def input(
    cls: T | None = None,
    *,
    name: str | None = None,
    one_of: bool | None = None,
    description: str | None = None,
    directives: Sequence[object] = (),
    inaccessible: bool = False,
    tags: Sequence[str] = (),
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
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    **federation_kwargs: Unpack[FederationInterfaceParams],
) -> T: ...


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def interface(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    **federation_kwargs: Unpack[FederationInterfaceParams],
) -> Callable[[T], T]: ...


def interface(
    cls: T | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    **federation_kwargs: Unpack[FederationInterfaceParams],
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        is_interface=True,
        **federation_kwargs,
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
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    **federation_kwargs: Unpack[FederationInterfaceParams],
) -> T: ...


@overload
@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(base_field, field, StrawberryField),
)
def interface_object(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    **federation_kwargs: Unpack[FederationInterfaceParams],
) -> Callable[[T], T]: ...


def interface_object(
    cls: T | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    **federation_kwargs: Unpack[FederationInterfaceParams],
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        is_interface=False,
        is_interface_object=True,
        **federation_kwargs,
    )


__all__ = ["input", "interface", "interface_object", "type"]
