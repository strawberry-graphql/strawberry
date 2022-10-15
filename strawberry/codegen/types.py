from __future__ import annotations

from dataclasses import dataclass
from enum import EnumMeta
from typing import Union

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
    types: list[GraphQLObjectType]


@dataclass
class GraphQLField:
    name: str
    alias: str | None
    type: GraphQLType


@dataclass
class GraphQLObjectType:
    name: str
    fields: list[GraphQLField]


@dataclass
class GraphQLEnum:
    name: str
    values: list[str]
    python_type: EnumMeta


@dataclass
class GraphQLScalar:
    name: str
    python_type: type | None


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
    alias: str | None
    selections: list[GraphQLSelection]
    directives: list[GraphQLDirective]
    arguments: list[GraphQLArgument]


@dataclass
class GraphQLInlineFragment:
    type_condition: str
    selections: list[GraphQLSelection]


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
    values: list[GraphQLArgumentValue]


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
    variables_type: GraphQLObjectType | None
