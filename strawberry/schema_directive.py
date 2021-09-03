import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Type


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
    wrap: Type
    graphql_name: Optional[str]
    locations: List[Location]
    description: Optional[str] = None

    def __call__(self, *args, **kwargs):
        return self  # self.wrap(*args, **kwargs)


def schema_directive(*, locations: List[Location], description=None, name=None):
    def _wrap(cls: Type) -> StrawberrySchemaDirective:
        return StrawberrySchemaDirective(
            python_name=cls.__name__,
            wrap=dataclass(cls),
            graphql_name=name,
            locations=locations,
            description=description,
        )

    return _wrap


__all__ = ["Location", "StrawberrySchemaDirective", "schema_directive"]
