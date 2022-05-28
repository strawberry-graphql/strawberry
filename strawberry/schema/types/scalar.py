import datetime
import decimal
from typing import Dict
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
        specified_by_url=definition.specified_by_url,
        serialize=definition.serialize,
        parse_value=definition.parse_value,
        parse_literal=definition.parse_literal,
    )


def _make_scalar_definition(scalar_type: GraphQLScalarType) -> ScalarDefinition:
    return ScalarDefinition(
        name=scalar_type.name,
        description=scalar_type.name,
        specified_by_url=scalar_type.specified_by_url,
        serialize=scalar_type.serialize,
        parse_literal=scalar_type.parse_literal,
        parse_value=scalar_type.parse_value,
        implementation=scalar_type,
    )


def _get_scalar_definition(scalar) -> ScalarDefinition:
    return scalar._scalar_definition


DEFAULT_SCALAR_REGISTRY: Dict[object, ScalarDefinition] = {
    type(None): _get_scalar_definition(base_scalars.Void),
    None: _get_scalar_definition(base_scalars.Void),
    str: _make_scalar_definition(GraphQLString),
    int: _make_scalar_definition(GraphQLInt),
    float: _make_scalar_definition(GraphQLFloat),
    bool: _make_scalar_definition(GraphQLBoolean),
    ID: _make_scalar_definition(GraphQLID),
    UUID: _get_scalar_definition(base_scalars.UUID),
    Upload: _get_scalar_definition(Upload),
    datetime.date: _get_scalar_definition(base_scalars.Date),
    datetime.datetime: _get_scalar_definition(base_scalars.DateTime),
    datetime.time: _get_scalar_definition(base_scalars.Time),
    decimal.Decimal: _get_scalar_definition(base_scalars.Decimal),
}
