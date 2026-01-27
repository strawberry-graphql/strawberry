import base64 as base64_lib
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

from strawberry.file_uploads.scalars import Upload, UploadDefinition
from strawberry.scalars import ID, JSON, Base16, Base32, Base64
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
        origin=scalar_type,
    )


DEFAULT_SCALAR_REGISTRY: dict[object, ScalarDefinition] = {
    type(None): base_scalars.VoidDefinition,
    None: base_scalars.VoidDefinition,
    str: _make_scalar_definition(GraphQLString),
    int: _make_scalar_definition(GraphQLInt),
    float: _make_scalar_definition(GraphQLFloat),
    bool: _make_scalar_definition(GraphQLBoolean),
    ID: _make_scalar_definition(GraphQLID),
    UUID: base_scalars.UUIDDefinition,
    Upload: UploadDefinition,
    datetime.date: base_scalars.DateDefinition,
    datetime.datetime: base_scalars.DateTimeDefinition,
    datetime.time: base_scalars.TimeDefinition,
    decimal.Decimal: base_scalars.DecimalDefinition,
    JSON: scalar(
        name="JSON",
        description=(
            "The `JSON` scalar type represents JSON values as specified by "
            "[ECMA-404]"
            "(https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf)."
        ),
        specified_by_url=(
            "https://ecma-international.org/wp-content/uploads/ECMA-404_2nd_edition_december_2017.pdf"
        ),
        serialize=lambda v: v,
        parse_value=lambda v: v,
    ),
    Base16: scalar(
        name="Base16",
        description="Represents binary data as Base16-encoded (hexadecimal) strings.",
        specified_by_url="https://datatracker.ietf.org/doc/html/rfc4648.html#section-8",
        serialize=lambda v: base64_lib.b16encode(v).decode("utf-8"),
        parse_value=lambda v: base64_lib.b16decode(v.encode("utf-8"), casefold=True),
    ),
    Base32: scalar(
        name="Base32",
        description=(
            "Represents binary data as Base32-encoded strings, using the standard alphabet."
        ),
        specified_by_url="https://datatracker.ietf.org/doc/html/rfc4648.html#section-6",
        serialize=lambda v: base64_lib.b32encode(v).decode("utf-8"),
        parse_value=lambda v: base64_lib.b32decode(v.encode("utf-8"), casefold=True),
    ),
    Base64: scalar(
        name="Base64",
        description=(
            "Represents binary data as Base64-encoded strings, using the standard alphabet."
        ),
        specified_by_url="https://datatracker.ietf.org/doc/html/rfc4648.html#section-4",
        serialize=lambda v: base64_lib.b64encode(v).decode("utf-8"),
        parse_value=lambda v: base64_lib.b64decode(v.encode("utf-8")),
    ),
}


__all__ = [
    "DEFAULT_SCALAR_REGISTRY",
    "_make_scalar_definition",
    "_make_scalar_type",
]
