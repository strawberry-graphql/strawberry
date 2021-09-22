from typing import List, Type, TypeVar

from strawberry.federation.schema_directives import Key
from strawberry.field import StrawberryField, field as base_field
from strawberry.object_type import type as base_type
from strawberry.utils.typing import __dataclass_transform__

from .field import field


T = TypeVar("T")


@__dataclass_transform__(
    order_default=True, field_descriptors=(base_field, field, StrawberryField)
)
def type(
    cls: Type = None,
    *,
    name: str = None,
    description: str = None,
    keys: List[str] = None,
    extend: bool = False,
):
    directives = [Key(key) for key in keys or []]

    return base_type(
        cls,
        name=name,
        description=description,
        directives=directives,  # type: ignore
        extend=extend,
    )
