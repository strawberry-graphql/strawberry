from typing import Any

import pytest
from graphql import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLField,
    GraphQLObjectType,
    SchemaMetaFieldDef,
    TypeMetaFieldDef,
    TypeNameMetaFieldDef,
    Undefined,
    introspection_types,
)

from strawberry.schema.name_converter import NameConverter
from strawberry.types.base import (
    StrawberryList,
    StrawberryOptional,
    get_object_definition,
)
from strawberry.types.enum import StrawberryEnumDefinition
from strawberry.types.field import StrawberryField
from strawberry.types.introspection import (
    INTROSPECTION_TYPES,
    IntrospectionDirectiveLocation,
    IntrospectionTypeKind,
    get_introspection_field,
)
from strawberry.types.unset import UNSET

META_FIELDS = {
    "__schema": SchemaMetaFieldDef,
    "__type": TypeMetaFieldDef,
    "__typename": TypeNameMetaFieldDef,
}


def _graphql_type_name(type_: Any, *, nullable: bool = False) -> str:
    """Print a Strawberry field type the way graphql-core prints its types."""
    if isinstance(type_, StrawberryOptional):
        return _graphql_type_name(type_.of_type, nullable=True)

    suffix = "" if nullable else "!"
    if isinstance(type_, StrawberryList):
        return f"[{_graphql_type_name(type_.of_type)}]{suffix}"
    if isinstance(type_, StrawberryEnumDefinition):
        return f"{type_.name}{suffix}"

    scalars = {str: "String", bool: "Boolean"}
    name = scalars.get(type_) or get_object_definition(type_, strict=True).name
    return f"{name}{suffix}"


def _graphql_default(argument: GraphQLArgument) -> Any:
    # graphql-core 3.3 stores some defaults in `default` instead of `default_value`
    if argument.default_value is not Undefined:
        return argument.default_value
    return argument.default.value if argument.default else Undefined


def _assert_field_matches(field: StrawberryField, graphql_field: GraphQLField) -> None:
    name_converter = NameConverter()

    assert _graphql_type_name(field.type) == str(graphql_field.type)
    assert {
        name_converter.get_graphql_name(argument): (
            _graphql_type_name(argument.type),
            Undefined if argument.default is UNSET else argument.default,
        )
        for argument in field.arguments
    } == {
        name: (str(argument.type), _graphql_default(argument))
        for name, argument in graphql_field.args.items()
    }


@pytest.mark.parametrize("type_", INTROSPECTION_TYPES, ids=lambda type_: type_.__name__)
def test_introspection_types_match_graphql_core(type_: type) -> None:
    definition = get_object_definition(type_, strict=True)
    graphql_type = introspection_types[definition.name]
    assert isinstance(graphql_type, GraphQLObjectType)

    name_converter = NameConverter()
    assert {name_converter.get_graphql_name(field) for field in definition.fields} == (
        set(graphql_type.fields)
    )

    for name, graphql_field in graphql_type.fields.items():
        _assert_field_matches(
            get_introspection_field(definition.name, name), graphql_field
        )


def test_introspection_types_cover_graphql_core() -> None:
    object_type_names = {
        get_object_definition(type_, strict=True).name for type_ in INTROSPECTION_TYPES
    }
    enum_type_names = {"__TypeKind", "__DirectiveLocation"}

    assert object_type_names | enum_type_names == set(introspection_types)


@pytest.mark.parametrize(
    "enum", [IntrospectionTypeKind, IntrospectionDirectiveLocation]
)
def test_introspection_enums_match_graphql_core(enum: Any) -> None:
    definition: StrawberryEnumDefinition = enum.__strawberry_definition__
    graphql_enum = introspection_types[definition.name]
    assert isinstance(graphql_enum, GraphQLEnumType)

    assert [value.name for value in definition.values] == list(graphql_enum.values)


@pytest.mark.parametrize("name", META_FIELDS)
def test_meta_fields_match_graphql_core(name: str) -> None:
    field = get_introspection_field("Query", name)

    _assert_field_matches(field, META_FIELDS[name])


def test_typename_is_found_on_introspection_types() -> None:
    assert get_introspection_field("__Type", "__typename") is (
        get_introspection_field("Query", "__typename")
    )


def test_unknown_field_raises() -> None:
    with pytest.raises(ValueError, match=r"Query\.missing is neither"):
        get_introspection_field("Query", "missing")
