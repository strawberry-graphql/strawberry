"""Strawberry definitions of GraphQL's introspection types.

graphql-core defines and resolves the introspection fields (``__schema``,
``__type``, ``__typename`` and the fields of ``__Type``, ``__Field``, ...), so
they have no ``StrawberryField``. These definitions give them one, so that
``Info`` works the same way for introspection fields as for any other field.

They are never added to a schema and their resolvers are never called.
"""

from __future__ import annotations

from enum import Enum
from functools import cache

from strawberry.schema.name_converter import NameConverter
from strawberry.types.base import get_object_definition
from strawberry.types.enum import enum
from strawberry.types.field import StrawberryField, field
from strawberry.types.object_type import type as strawberry_type


@enum(name="__TypeKind")
class IntrospectionTypeKind(Enum):
    SCALAR = "SCALAR"
    OBJECT = "OBJECT"
    INTERFACE = "INTERFACE"
    UNION = "UNION"
    ENUM = "ENUM"
    INPUT_OBJECT = "INPUT_OBJECT"
    LIST = "LIST"
    NON_NULL = "NON_NULL"


@enum(name="__DirectiveLocation")
class IntrospectionDirectiveLocation(Enum):
    QUERY = "QUERY"
    MUTATION = "MUTATION"
    SUBSCRIPTION = "SUBSCRIPTION"
    FIELD = "FIELD"
    FRAGMENT_DEFINITION = "FRAGMENT_DEFINITION"
    FRAGMENT_SPREAD = "FRAGMENT_SPREAD"
    INLINE_FRAGMENT = "INLINE_FRAGMENT"
    VARIABLE_DEFINITION = "VARIABLE_DEFINITION"
    FRAGMENT_VARIABLE_DEFINITION = "FRAGMENT_VARIABLE_DEFINITION"
    SCHEMA = "SCHEMA"
    SCALAR = "SCALAR"
    OBJECT = "OBJECT"
    FIELD_DEFINITION = "FIELD_DEFINITION"
    ARGUMENT_DEFINITION = "ARGUMENT_DEFINITION"
    INTERFACE = "INTERFACE"
    UNION = "UNION"
    ENUM = "ENUM"
    ENUM_VALUE = "ENUM_VALUE"
    INPUT_OBJECT = "INPUT_OBJECT"
    INPUT_FIELD_DEFINITION = "INPUT_FIELD_DEFINITION"
    DIRECTIVE_DEFINITION = "DIRECTIVE_DEFINITION"


@strawberry_type(name="__Schema")
class IntrospectionSchema:
    description: str | None
    types: list[IntrospectionType]
    query_type: IntrospectionType
    mutation_type: IntrospectionType | None
    subscription_type: IntrospectionType | None

    @field
    def directives(
        self, include_deprecated: bool = False
    ) -> list[IntrospectionDirective]:
        raise NotImplementedError


@strawberry_type(name="__Type")
class IntrospectionType:
    kind: IntrospectionTypeKind
    name: str | None
    description: str | None
    specified_by_url: str | None = field(name="specifiedByURL")

    @field
    def fields(
        self, include_deprecated: bool = False
    ) -> list[IntrospectionField] | None:
        raise NotImplementedError

    interfaces: list[IntrospectionType] | None
    possible_types: list[IntrospectionType] | None

    @field
    def enum_values(
        self, include_deprecated: bool = False
    ) -> list[IntrospectionEnumValue] | None:
        raise NotImplementedError

    @field
    def input_fields(
        self, include_deprecated: bool = False
    ) -> list[IntrospectionInputValue] | None:
        raise NotImplementedError

    of_type: IntrospectionType | None
    is_one_of: bool | None


@strawberry_type(name="__Field")
class IntrospectionField:
    name: str
    description: str | None

    @field
    def args(self, include_deprecated: bool = False) -> list[IntrospectionInputValue]:
        raise NotImplementedError

    type_: IntrospectionType = field(name="type")
    is_deprecated: bool
    deprecation_reason: str | None


@strawberry_type(name="__InputValue")
class IntrospectionInputValue:
    name: str
    description: str | None
    type_: IntrospectionType = field(name="type")
    default_value: str | None
    is_deprecated: bool
    deprecation_reason: str | None


@strawberry_type(name="__EnumValue")
class IntrospectionEnumValue:
    name: str
    description: str | None
    is_deprecated: bool
    deprecation_reason: str | None


@strawberry_type(name="__Directive")
class IntrospectionDirective:
    name: str
    description: str | None
    is_repeatable: bool
    locations: list[IntrospectionDirectiveLocation]

    @field
    def args(self, include_deprecated: bool = False) -> list[IntrospectionInputValue]:
        raise NotImplementedError

    is_deprecated: bool
    deprecation_reason: str | None


# The fields graphql-core adds to object types: `__schema` and `__type` on the
# query type, `__typename` on every object type. This is not a GraphQL type.
@strawberry_type(name="IntrospectionMetaFields")
class IntrospectionMetaFields:
    schema: IntrospectionSchema = field(name="__schema")

    @field(name="__type")
    def type_(self, name: str) -> IntrospectionType | None:
        raise NotImplementedError

    typename: str = field(name="__typename")


INTROSPECTION_TYPES = (
    IntrospectionSchema,
    IntrospectionType,
    IntrospectionField,
    IntrospectionInputValue,
    IntrospectionEnumValue,
    IntrospectionDirective,
)


@cache
def _get_introspection_fields() -> dict[tuple[str | None, str], StrawberryField]:
    # Introspection names are fixed, whatever the schema's name converter does.
    name_converter = NameConverter()
    fields: dict[tuple[str | None, str], StrawberryField] = {}

    for type_ in INTROSPECTION_TYPES:
        definition = get_object_definition(type_, strict=True)
        for type_field in definition.fields:
            graphql_name = name_converter.get_graphql_name(type_field)
            fields[definition.name, graphql_name] = type_field

    meta_definition = get_object_definition(IntrospectionMetaFields, strict=True)
    for meta_field in meta_definition.fields:
        fields[None, name_converter.get_graphql_name(meta_field)] = meta_field

    return fields


def get_introspection_field(type_name: str, field_name: str) -> StrawberryField:
    """Return the Strawberry definition of a graphql-core introspection field."""
    fields = _get_introspection_fields()
    # `__typename` is available on every type, introspection types included.
    introspection_field = fields.get((None, field_name)) or fields.get(
        (type_name, field_name)
    )
    if introspection_field is None:
        raise ValueError(
            f"{type_name}.{field_name} is neither a Strawberry field nor a GraphQL "
            "introspection field."
        )
    return introspection_field


__all__ = [
    "INTROSPECTION_TYPES",
    "get_introspection_field",
]
