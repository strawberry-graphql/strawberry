import datetime
import decimal
from typing import Dict, Type, cast

from graphql import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLID,
    GraphQLInt,
    GraphQLScalarType,
    GraphQLString,
)

from strawberry.custom_scalar import SCALAR_REGISTRY, ScalarDefinition
from strawberry.file_uploads.scalars import Upload
from strawberry.scalars import ID

from .base_scalars import UUID, Date, DateTime, Decimal, Time
from .types import ConcreteType, TypeMap


def _make_scalar_type(definition: ScalarDefinition) -> GraphQLScalarType:
    return GraphQLScalarType(
        name=definition.name,
        description=definition.description,
        serialize=definition.serialize,
        parse_value=definition.parse_value,
        parse_literal=definition.parse_literal,
    )


DEFAULT_SCALAR_REGISTRY: Dict[Type, GraphQLScalarType] = {
    str: GraphQLString,
    int: GraphQLInt,
    float: GraphQLFloat,
    bool: GraphQLBoolean,
    ID: GraphQLID,
    UUID: _make_scalar_type(UUID._scalar_definition),
    Upload: _make_scalar_type(Upload._scalar_definition),
    datetime.date: _make_scalar_type(Date._scalar_definition),
    datetime.datetime: _make_scalar_type(DateTime._scalar_definition),
    datetime.time: _make_scalar_type(Time._scalar_definition),
    decimal.Decimal: _make_scalar_type(Decimal._scalar_definition),
}


def get_scalar_type(annotation: Type, type_map: TypeMap) -> GraphQLScalarType:
    if annotation in DEFAULT_SCALAR_REGISTRY:
        return DEFAULT_SCALAR_REGISTRY[annotation]

    if annotation in SCALAR_REGISTRY:
        scalar_definition = SCALAR_REGISTRY[annotation]
    else:
        scalar_definition = annotation._scalar_definition

    if scalar_definition.name not in type_map:
        type_map[scalar_definition.name] = ConcreteType(
            definition=scalar_definition,
            implementation=_make_scalar_type(scalar_definition),
        )

    return cast(GraphQLScalarType, type_map[scalar_definition.name].implementation)
