import dataclasses
from enum import Enum
from typing import Callable, List, Optional, Type, TypeVar
from typing_extensions import dataclass_transform

from strawberry.types.field import StrawberryField, field
from strawberry.types.object_type import _wrap_dataclass
from strawberry.types.type_resolver import _get_fields

from .directive import directive_field


class Location(Enum):
    SCHEMA = "schema"
    SCALAR = "scalar"
    OBJECT = "object"
    FIELD_DEFINITION = "field definition"
    ARGUMENT_DEFINITION = "argument definition"
    INTERFACE = "interface"
    UNION = "union"
    ENUM = "enum"
    ENUM_VALUE = "enum value"
    INPUT_OBJECT = "input object"
    INPUT_FIELD_DEFINITION = "input field definition"


@dataclasses.dataclass
class StrawberrySchemaDirective:
    python_name: str
    graphql_name: Optional[str]
    locations: List[Location]
    fields: List["StrawberryField"]
    description: Optional[str] = None
    repeatable: bool = False
    print_definition: bool = True
    origin: Optional[Type] = None


T = TypeVar("T", bound=Type)


@dataclass_transform(
    order_default=True,
    kw_only_default=True,
    field_specifiers=(directive_field, field, StrawberryField),
)
def schema_directive(
    *,
    locations: List[Location],
    description: Optional[str] = None,
    name: Optional[str] = None,
    repeatable: bool = False,
    print_definition: bool = True,
) -> Callable[..., T]:
    def _wrap(cls: T) -> T:
        cls = _wrap_dataclass(cls)  # type: ignore
        fields = _get_fields(cls, {})

        cls.__strawberry_directive__ = StrawberrySchemaDirective(
            python_name=cls.__name__,
            graphql_name=name,
            locations=locations,
            description=description,
            repeatable=repeatable,
            fields=fields,
            print_definition=print_definition,
            origin=cls,
        )

        return cls

    return _wrap


__all__ = ["Location", "StrawberrySchemaDirective", "schema_directive"]
