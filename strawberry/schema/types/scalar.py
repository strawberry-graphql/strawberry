import datetime
import decimal
from typing import Dict, Type
from uuid import UUID

from graphql import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLID,
    GraphQLInt,
    GraphQLScalarType,
    GraphQLString,
)

from strawberry.custom_scalar import ScalarDefinition
from strawberry.file_uploads.scalars import Upload
from strawberry.scalars import ID
from strawberry.schema.types import base_scalars


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
    UUID: _make_scalar_type(base_scalars.UUID._scalar_definition),
    Upload: _make_scalar_type(Upload._scalar_definition),
    datetime.date: _make_scalar_type(base_scalars.Date._scalar_definition),
    datetime.datetime: _make_scalar_type(base_scalars.DateTime._scalar_definition),
    datetime.time: _make_scalar_type(base_scalars.Time._scalar_definition),
    decimal.Decimal: _make_scalar_type(base_scalars.Decimal._scalar_definition),
}
