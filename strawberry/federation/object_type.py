from typing import TYPE_CHECKING, Callable, Iterable, Sequence, TypeVar, Union, overload

from strawberry.field import StrawberryField, field as base_field
from strawberry.object_type import type as base_type
from strawberry.unset import UNSET
from strawberry.utils.typing import __dataclass_transform__

from .field import field


if TYPE_CHECKING:
    from .schema_directives import Key


T = TypeVar("T")


def _impl_type(
    cls: T,
    *,
    name: str = None,
    description: str = None,
    directives: Iterable[object] = (),
    keys: Iterable[Union["Key", str]] = (),
    extend: bool = False,
    shareable: bool = False,
    inaccessible: bool = UNSET,
    is_input: bool = False,
    is_interface: bool = False,
) -> T:
    from strawberry.federation.schema_directives import Inaccessible, Key, Shareable

    all_directives = [Key(key, UNSET) if isinstance(key, str) else key for key in keys]

    if shareable:
        all_directives.append(Shareable())  # type: ignore

    if inaccessible is not UNSET:
        all_directives.append(Inaccessible())  # type: ignore
    all_directives.extend(directives)  # type: ignore

    return base_type(
        cls,
        name=name,
        description=description,
        directives=all_directives,
        extend=extend,
        is_input=is_input,
        is_interface=is_interface,
    )


@overload
@__dataclass_transform__(
    order_default=True, field_descriptors=(base_field, field, StrawberryField)
)
def type(
    cls: T,
    *,
    name: str = None,
    description: str = None,
    keys: Iterable[Union["Key", str]] = (),
    inaccessible: bool = UNSET,
    extend: bool = False,
) -> T:
    ...


@overload
@__dataclass_transform__(
    order_default=True, field_descriptors=(base_field, field, StrawberryField)
)
def type(
    *,
    name: str = None,
    description: str = None,
    keys: Iterable[Union["Key", str]] = (),
    inaccessible: bool = UNSET,
    extend: bool = False,
    shareable: bool = False,
) -> Callable[[T], T]:
    ...


def type(
    cls=None,
    *,
    name=None,
    description=None,
    directives: Iterable[object] = (),
    keys: Iterable[Union["Key", str]] = (),
    extend=False,
    shareable: bool = False,
    inaccessible: bool = UNSET,
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
    )


@overload
@__dataclass_transform__(order_default=True, field_descriptors=(field, StrawberryField))
def input(
    cls: T,
    *,
    name: str = None,
    description: str = None,
    directives: Sequence[object] = (),
    inaccessible: bool = UNSET,
) -> T:
    ...


@overload
@__dataclass_transform__(order_default=True, field_descriptors=(field, StrawberryField))
def input(
    *,
    name: str = None,
    description: str = None,
    directives: Sequence[object] = (),
    inaccessible: bool = UNSET,
) -> Callable[[T], T]:
    ...


def input(
    cls=None,
    *,
    name=None,
    description=None,
    inaccessible: bool = UNSET,
    directives=(),
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        inaccessible=inaccessible,
        is_input=True,
    )


# TODO: fix type hints
@__dataclass_transform__(order_default=True, field_descriptors=(field, StrawberryField))
def interface(
    cls: T = None,
    *,
    name: str = None,
    description: str = None,
    directives: Iterable[object] = (),
    keys: Iterable[Union["Key", str]] = (),
    inaccessible: bool = UNSET,
):
    return _impl_type(
        cls,
        name=name,
        description=description,
        directives=directives,
        keys=keys,
        inaccessible=inaccessible,
        is_interface=True,
    )
