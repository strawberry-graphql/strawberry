from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Mapping, Optional, Type, Union

if TYPE_CHECKING:
    from enum import EnumMeta
    from typing_extensions import Literal

    from strawberry.unset import UnsetType


@dataclass
class GraphQLOptional:
    of_type: GraphQLType


@dataclass
class GraphQLList:
    of_type: GraphQLType


@dataclass
class GraphQLUnion:
    name: str
    types: List[GraphQLObjectType]


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
    fields: List[GraphQLField] = field(default_factory=list)
    graphql_typename: Optional[str] = None


# Subtype of GraphQLObjectType.
# Because dataclass inheritance is a little odd, the fields are
# repeated here.
@dataclass
class GraphQLFragmentType(GraphQLObjectType):
    name: str
    fields: List[GraphQLField] = field(default_factory=list)
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
    values: List[str]
    python_type: EnumMeta


@dataclass
class GraphQLScalar:
    name: str
    python_type: Optional[Type]


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
    selections: List[GraphQLSelection]
    directives: List[GraphQLDirective]
    arguments: List[GraphQLArgument]


@dataclass
class GraphQLInlineFragment:
    type_condition: str
    selections: List[GraphQLSelection]


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
    values: List[GraphQLArgumentValue]


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
    arguments: List[GraphQLArgument]


@dataclass
class GraphQLVariable:
    name: str
    type: GraphQLType


@dataclass
class GraphQLOperation:
    name: str
    kind: Literal["query", "mutation", "subscription"]
    selections: List[GraphQLSelection]
    directives: List[GraphQLDirective]
    variables: List[GraphQLVariable]
    type: GraphQLObjectType
    variables_type: Optional[GraphQLObjectType]
