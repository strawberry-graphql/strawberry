import dataclasses
from typing import Dict, Union

from graphql import GraphQLField, GraphQLInputField, GraphQLType  # noqa

from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition
from strawberry.type import TypeDefinition
from strawberry.union import StrawberryUnion


Field = Union[GraphQLInputField, GraphQLField]


@dataclasses.dataclass
class ConcreteType:
    definition: Union[TypeDefinition, EnumDefinition, ScalarDefinition, StrawberryUnion]
    implementation: GraphQLType


TypeMap = Dict[str, ConcreteType]
