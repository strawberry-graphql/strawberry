import dataclasses
from typing import Dict, Union

from graphql import GraphQLField, GraphQLInputField, GraphQLType

from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion


Field = Union[GraphQLInputField, GraphQLField]


@dataclasses.dataclass
class ConcreteType:
    definition: Union[TypeDefinition, EnumDefinition, ScalarDefinition, StrawberryUnion]
    implementation: GraphQLType


TypeMap = Dict[str, ConcreteType]


__all__ = ["ConcreteType", "Field", "GraphQLType", "TypeMap"]
