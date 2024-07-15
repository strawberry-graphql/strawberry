from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Dict, Union

from graphql import GraphQLField, GraphQLInputField, GraphQLType

if TYPE_CHECKING:
    from strawberry.types.base import StrawberryObjectDefinition
    from strawberry.types.enum import EnumDefinition
    from strawberry.types.scalar import ScalarDefinition
    from strawberry.types.union import StrawberryUnion

Field = Union[GraphQLInputField, GraphQLField]


@dataclasses.dataclass
class ConcreteType:
    definition: Union[
        StrawberryObjectDefinition, EnumDefinition, ScalarDefinition, StrawberryUnion
    ]
    implementation: GraphQLType


TypeMap = Dict[str, ConcreteType]


__all__ = ["ConcreteType", "Field", "GraphQLType", "TypeMap"]
