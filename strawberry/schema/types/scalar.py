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
        serialize=definition.serialize,
        parse_value=definition.parse_value,
        parse_literal=definition.parse_literal,
    )


def _make_scalar_definition(scalar_type: GraphQLScalarType) -> ScalarDefinition:
    return ScalarDefinition(
        name=scalar_type.name,
        description=scalar_type.name,
        serialize=scalar_type.serialize,
        parse_literal=scalar_type.parse_literal,
        parse_value=scalar_type.parse_value,
        implementation=scalar_type,
    )


DEFAULT_SCALAR_REGISTRY: Dict[object, ScalarDefinition] = {
    str: _make_scalar_definition(GraphQLString),
    int: _make_scalar_definition(GraphQLInt),
    float: _make_scalar_definition(GraphQLFloat),
    bool: _make_scalar_definition(GraphQLBoolean),
    ID: _make_scalar_definition(GraphQLID),
    UUID: base_scalars.UUID._scalar_definition,
    Upload: Upload._scalar_definition,
    datetime.date: base_scalars.Date._scalar_definition,
    datetime.datetime: base_scalars.DateTime._scalar_definition,
    datetime.time: base_scalars.Time._scalar_definition,
    decimal.Decimal: base_scalars.Decimal._scalar_definition,
}
