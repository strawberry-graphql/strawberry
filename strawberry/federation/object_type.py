from typing import Callable, List, TypeVar, overload

from strawberry.field import StrawberryField, field as base_field
from strawberry.object_type import type as base_type
from strawberry.utils.typing import __dataclass_transform__

from .field import field


T = TypeVar("T")


@overload
@__dataclass_transform__(
    order_default=True, field_descriptors=(base_field, field, StrawberryField)
)
def type(
    cls: T,
    *,
    name: str = None,
    description: str = None,
    keys: List[str] = None,
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
    keys: List[str] = None,
    extend: bool = False,
) -> Callable[[T], T]:
    ...


def type(
    cls=None,
    *,
    name=None,
    description=None,
    keys=None,
    extend=False,
):
    from strawberry.federation.schema_directives import Key

    directives = [Key(key) for key in keys or []]

    return base_type(
        cls,
        name=name,
        description=description,
        directives=directives,  # type: ignore[arg-type]
        extend=extend,
    )
