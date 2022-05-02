import dataclasses
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Type, TypeVar

from strawberry.object_type import _wrap_dataclass
from strawberry.types.type_resolver import _get_fields


if TYPE_CHECKING:
    from strawberry.field import StrawberryField


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


T = TypeVar("T", bound=Type)


def schema_directive(*, locations: List[Location], description=None, name=None):
    def _wrap(cls: T) -> T:
        cls = _wrap_dataclass(cls)
        fields = _get_fields(cls)

        cls.__strawberry_directive__ = StrawberrySchemaDirective(
            python_name=cls.__name__,
            graphql_name=name,
            locations=locations,
            description=description,
            fields=fields,
        )

        return cls

    return _wrap


__all__ = ["Location", "StrawberrySchemaDirective", "schema_directive"]
