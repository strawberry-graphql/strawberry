from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, TypeAlias

from graphql import GraphQLField, GraphQLInputField, GraphQLType

if TYPE_CHECKING:
    from strawberry.types.base import StrawberryObjectDefinition
    from strawberry.types.enum import StrawberryEnumDefinition
    from strawberry.types.scalar import ScalarDefinition
    from strawberry.types.union import StrawberryUnion

Field: TypeAlias = GraphQLInputField | GraphQLField


@dataclasses.dataclass
class ConcreteType:
    definition: (
        StrawberryObjectDefinition
        | StrawberryEnumDefinition
        | ScalarDefinition
        | StrawberryUnion
    )
    implementation: GraphQLType


TypeMap = dict[str, ConcreteType]


__all__ = ["ConcreteType", "Field", "GraphQLType", "TypeMap"]
