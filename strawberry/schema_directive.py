import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Type

from strawberry.utils.mixins import GraphQLNameMixin


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
class StrawberrySchemaDirective(GraphQLNameMixin):
    wrap: Type
    python_name: str
    graphql_name: Optional[str]
    locations: List[Location]
    description: Optional[str] = None
    instance: Optional[object] = dataclasses.field(init=False)

    def get_graphql_name(self, auto_camel_case: bool) -> str:
        if self.graphql_name is not None:
            return self.graphql_name

        assert self.python_name

        if auto_camel_case:
            # we don't want the first letter to be uppercase
            return self.python_name[0].lower() + self.python_name[1:]

        return self.python_name

    def __call__(self, *args, **kwargs):
        self.instance = self.wrap(*args, **kwargs)

        return self


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
