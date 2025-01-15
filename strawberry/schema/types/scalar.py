import datetime
import decimal
from uuid import UUID

from graphql import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLID,
    GraphQLInt,
    GraphQLScalarType,
    GraphQLString,
)

from strawberry.file_uploads.scalars import Upload
from strawberry.relay.types import GlobalID
from strawberry.scalars import ID
from strawberry.schema.types import base_scalars
from strawberry.types.scalar import ScalarDefinition, scalar


def _make_scalar_type(definition: ScalarDefinition) -> GraphQLScalarType:
    from strawberry.schema.schema_converter import GraphQLCoreConverter

    return GraphQLScalarType(
        name=definition.name,
        description=definition.description,
        specified_by_url=definition.specified_by_url,
        serialize=definition.serialize,
        parse_value=definition.parse_value,
        parse_literal=definition.parse_literal,
        extensions={GraphQLCoreConverter.DEFINITION_BACKREF: definition},
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


def _get_scalar_definition(scalar: type) -> ScalarDefinition:
    return scalar._scalar_definition  # type: ignore[attr-defined]


DEFAULT_SCALAR_REGISTRY: dict[object, ScalarDefinition] = {
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
    # We can't wrap GlobalID with @scalar because it has custom attributes/methods
    GlobalID: _get_scalar_definition(
        scalar(
            GlobalID,
            name="GlobalID",
            description=GraphQLID.description,
            parse_literal=lambda v, vars=None: GlobalID.from_id(  # noqa: A006
                GraphQLID.parse_literal(v, vars)
            ),
            parse_value=GlobalID.from_id,
            serialize=str,
            specified_by_url=("https://relay.dev/graphql/objectidentification.htm"),
        )
    ),
}

__all__ = [
    "DEFAULT_SCALAR_REGISTRY",
    "_get_scalar_definition",
    "_make_scalar_definition",
    "_make_scalar_type",
]
