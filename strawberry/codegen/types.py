from __future__ import annotations

from dataclasses import dataclass
from enum import EnumMeta
from typing import List, Optional, Type, Union

from typing_extensions import Literal


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


@dataclass
class GraphQLObjectType:
    name: str
    fields: List[GraphQLField]


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


GraphQLSelection = Union[GraphQLFieldSelection, GraphQLInlineFragment]


@dataclass
class GraphQLStringValue:
    value: str


@dataclass
class GraphQLIntValue:
    value: int


@dataclass
class GraphQLEnumValue:
    name: str


@dataclass
class GraphQLBoolValue:
    value: bool


@dataclass
class GraphQLListValue:
    values: List[GraphQLArgumentValue]


@dataclass
class GraphQLVariableReference:
    value: str


GraphQLArgumentValue = Union[
    GraphQLStringValue,
    GraphQLIntValue,
    GraphQLVariableReference,
    GraphQLListValue,
    GraphQLEnumValue,
    GraphQLBoolValue,
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
