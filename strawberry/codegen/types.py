from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from collections.abc import Mapping
    from enum import EnumMeta
    from typing_extensions import Literal

    from strawberry.types.unset import UnsetType


@dataclass
class GraphQLOptional:
    of_type: GraphQLType


@dataclass
class GraphQLList:
    of_type: GraphQLType


@dataclass
class GraphQLUnion:
    name: str
    types: list[GraphQLObjectType]


@dataclass
class GraphQLField:
    name: str
    alias: Optional[str]
    type: GraphQLType
    default_value: Optional[GraphQLArgumentValue] = None


@dataclass
class GraphQLFragmentSpread:
    name: str


@dataclass
class GraphQLObjectType:
    name: str
    fields: list[GraphQLField] = field(default_factory=list)
    graphql_typename: Optional[str] = None


# Subtype of GraphQLObjectType.
# Because dataclass inheritance is a little odd, the fields are
# repeated here.
@dataclass
class GraphQLFragmentType(GraphQLObjectType):
    name: str
    fields: list[GraphQLField] = field(default_factory=list)
    graphql_typename: Optional[str] = None
    on: str = ""

    def __post_init__(self) -> None:
        if not self.on:
            raise ValueError(
                "GraphQLFragmentType must be constructed with a valid 'on'"
            )


@dataclass
class GraphQLEnum:
    name: str
    values: list[str]
    python_type: EnumMeta


@dataclass
class GraphQLScalar:
    name: str
    python_type: Optional[type]


GraphQLType = Union[
    GraphQLObjectType,
    GraphQLEnum,
    GraphQLScalar,
    GraphQLOptional,
    GraphQLList,
    GraphQLUnion,
]


@dataclass
class GraphQLFieldSelection:
    field: str
    alias: Optional[str]
    selections: list[GraphQLSelection]
    directives: list[GraphQLDirective]
    arguments: list[GraphQLArgument]


@dataclass
class GraphQLInlineFragment:
    type_condition: str
    selections: list[GraphQLSelection]


GraphQLSelection = Union[
    GraphQLFieldSelection, GraphQLInlineFragment, GraphQLFragmentSpread
]


@dataclass
class GraphQLStringValue:
    value: str


@dataclass
class GraphQLIntValue:
    value: int


@dataclass
class GraphQLFloatValue:
    value: float


@dataclass
class GraphQLEnumValue:
    name: str
    enum_type: Optional[str] = None


@dataclass
class GraphQLBoolValue:
    value: bool


@dataclass
class GraphQLNullValue:
    """A class that represents a GraphQLNull value."""

    value: None | UnsetType = None


@dataclass
class GraphQLListValue:
    values: list[GraphQLArgumentValue]


@dataclass
class GraphQLObjectValue:
    values: Mapping[str, GraphQLArgumentValue]


@dataclass
class GraphQLVariableReference:
    value: str


GraphQLArgumentValue = Union[
    GraphQLStringValue,
    GraphQLNullValue,
    GraphQLIntValue,
    GraphQLVariableReference,
    GraphQLFloatValue,
    GraphQLListValue,
    GraphQLEnumValue,
    GraphQLBoolValue,
    GraphQLObjectValue,
]


@dataclass
class GraphQLArgument:
    name: str
    value: GraphQLArgumentValue


@dataclass
class GraphQLDirective:
    name: str
    arguments: list[GraphQLArgument]


@dataclass
class GraphQLVariable:
    name: str
    type: GraphQLType


@dataclass
class GraphQLOperation:
    name: str
    kind: Literal["query", "mutation", "subscription"]
    selections: list[GraphQLSelection]
    directives: list[GraphQLDirective]
    variables: list[GraphQLVariable]
    type: GraphQLObjectType
    variables_type: Optional[GraphQLObjectType]


__all__ = [
    "GraphQLArgument",
    "GraphQLArgumentValue",
    "GraphQLBoolValue",
    "GraphQLDirective",
    "GraphQLEnum",
    "GraphQLEnumValue",
    "GraphQLField",
    "GraphQLFieldSelection",
    "GraphQLFloatValue",
    "GraphQLFragmentSpread",
    "GraphQLFragmentType",
    "GraphQLInlineFragment",
    "GraphQLIntValue",
    "GraphQLList",
    "GraphQLListValue",
    "GraphQLNullValue",
    "GraphQLObjectType",
    "GraphQLObjectValue",
    "GraphQLOperation",
    "GraphQLOptional",
    "GraphQLScalar",
    "GraphQLSelection",
    "GraphQLStringValue",
    "GraphQLType",
    "GraphQLUnion",
    "GraphQLVariable",
    "GraphQLVariableReference",
]
