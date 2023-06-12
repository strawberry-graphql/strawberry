from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Dict, Union

from graphql import GraphQLField, GraphQLInputField, GraphQLType

if TYPE_CHECKING:
    from strawberry.custom_scalar import ScalarDefinition
    from strawberry.enum import EnumDefinition
    from strawberry.types.types import StrawberryObjectDefinition
    from strawberry.union import StrawberryUnion

Field = Union[GraphQLInputField, GraphQLField]


@dataclasses.dataclass
class ConcreteType:
    definition: Union[
        StrawberryObjectDefinition, EnumDefinition, ScalarDefinition, StrawberryUnion
    ]
    implementation: GraphQLType


TypeMap = Dict[str, ConcreteType]


__all__ = ["ConcreteType", "Field", "GraphQLType", "TypeMap"]
