from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Optional

from graphql import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLScalarType,
    GraphQLUnionType,
    is_union_type,
)
from graphql.type import (
    is_enum_type,
    is_input_type,
    is_interface_type,
    is_object_type,
    is_scalar_type,
    is_specified_directive,
)
from graphql.utilities.print_schema import (
    is_defined_type,
    print_block,
    print_deprecated,
    print_description,
    print_implemented_interfaces,
    print_specified_by_url,
    print_type as original_print_type,
)

from strawberry.field import StrawberryField
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.schema_directive import Location

from .print_args import print_args
from .print_directive_definition import print_directive_definition
from .print_extras import PrintExtras
from .print_input_value import print_input_value
from .print_schema_directives import print_schema_directive, print_schema_directives


if TYPE_CHECKING:
    from strawberry.schema import BaseSchema


def print_field_directives(
    field: Optional[StrawberryField], schema: BaseSchema, *, extras: PrintExtras
) -> str:
    if not field:
        return ""

    directives = (
        directive
        for directive in field.directives
        if any(
            location in [Location.FIELD_DEFINITION, Location.INPUT_FIELD_DEFINITION]
            for location in directive.__strawberry_directive__.locations  # type: ignore
        )
    )

    return "".join(
        (
            print_schema_directive(directive, schema=schema, extras=extras)
            for directive in directives
        )
    )


def print_argument_directives(
    argument: GraphQLArgument, *, schema: BaseSchema, extras: PrintExtras
) -> str:
    strawberry_type = argument.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    return "".join(
        (
            print_schema_directive(directive, schema=schema, extras=extras)
            for directive in directives
        )
    )


def print_fields(type_, schema: BaseSchema, *, extras: PrintExtras) -> str:
    fields = []

    for i, (name, field) in enumerate(type_.fields.items()):
        strawberry_field = field.extensions and field.extensions.get(
            GraphQLCoreConverter.DEFINITION_BACKREF
        )

        args = (
            print_args(field.args, "  ", schema=schema, extras=extras)
            if hasattr(field, "args")
            else ""
        )

        fields.append(
            print_description(field, "  ", not i)
            + f"  {name}"
            + args
            + f": {field.type}"
            + print_field_directives(strawberry_field, schema=schema, extras=extras)
            + print_deprecated(field.deprecation_reason)
        )

    return print_block(fields)


def print_scalar(
    type_: GraphQLScalarType, *, schema: BaseSchema, extras: PrintExtras
) -> str:
    printed_directives = print_schema_directives(type_, schema=schema, extras=extras)

    return (
        print_description(type_)
        + f"scalar {type_.name}"
        + print_specified_by_url(type_)
        + printed_directives
    ).strip()


def print_enum_value(
    name: str,
    value: GraphQLEnumValue,
    first_in_block,
    *,
    schema: BaseSchema,
    extras: PrintExtras,
) -> str:
    printed_directives = print_schema_directives(value, schema=schema, extras=extras)

    return (
        print_description(value, "  ", first_in_block)
        + f"  {name}"
        + print_deprecated(value.deprecation_reason)
        + printed_directives
    )


def print_enum(
    type_: GraphQLEnumType, *, schema: BaseSchema, extras: PrintExtras
) -> str:

    printed_directives = print_schema_directives(type_, schema=schema, extras=extras)

    values = [
        print_enum_value(name, value, not i, schema=schema, extras=extras)
        for i, (name, value) in enumerate(type_.values.items())
    ]
    return (
        print_description(type_)
        + f"enum {type_.name}"
        + printed_directives
        + print_block(values)
    )


def print_extends(type_, schema: BaseSchema):
    strawberry_type = type_.extensions and type_.extensions.get(
        GraphQLCoreConverter.DEFINITION_BACKREF
    )

    if strawberry_type and strawberry_type.extend:
        return "extend "

    return ""


def print_type_directives(type_, schema: BaseSchema, *, extras: PrintExtras) -> str:
    strawberry_type = type_.extensions and type_.extensions.get(
        GraphQLCoreConverter.DEFINITION_BACKREF
    )

    if not strawberry_type:
        return ""

    allowed_locations = (
        [Location.INPUT_OBJECT] if strawberry_type.is_input else [Location.OBJECT]
    )

    directives = (
        directive
        for directive in strawberry_type.directives or []
        if any(
            location in allowed_locations
            for location in directive.__strawberry_directive__.locations
        )
    )

    return "".join(
        (
            print_schema_directive(directive, schema=schema, extras=extras)
            for directive in directives
        )
    )


def _print_object(type_, schema: BaseSchema, *, extras: PrintExtras) -> str:
    return (
        print_description(type_)
        + print_extends(type_, schema)
        + f"type {type_.name}"
        + print_implemented_interfaces(type_)
        + print_type_directives(type_, schema, extras=extras)
        + print_fields(type_, schema, extras=extras)
    )


def _print_interface(type_, schema: BaseSchema, *, extras: PrintExtras) -> str:
    return (
        print_description(type_)
        + print_extends(type_, schema)
        + f"interface {type_.name}"
        + print_implemented_interfaces(type_)
        + print_type_directives(type_, schema, extras=extras)
        + print_fields(type_, schema, extras=extras)
    )


def _print_input_object(type_, schema: BaseSchema, *, extras: PrintExtras) -> str:
    fields = [
        print_description(field, "  ", not i) + "  " + print_input_value(name, field)
        for i, (name, field) in enumerate(type_.fields.items())
    ]
    return (
        print_description(type_)
        + f"input {type_.name}"
        + print_type_directives(type_, schema, extras=extras)
        + print_block(fields)
    )


def print_union(
    type_: GraphQLUnionType, *, schema: BaseSchema, extras: PrintExtras
) -> str:
    printed_directives = print_schema_directives(type_, schema=schema, extras=extras)

    types = type_.types
    possible_types = " = " + " | ".join(t.name for t in types) if types else ""
    return (
        print_description(type_)
        + f"union {type_.name}{printed_directives}"
        + possible_types
    )


def _print_type(type_, schema: BaseSchema, *, extras: PrintExtras) -> str:
    # prevents us from trying to print a scalar as an input type
    if is_scalar_type(type_):
        return print_scalar(type_, schema=schema, extras=extras)

    if is_enum_type(type_):
        return print_enum(type_, schema=schema, extras=extras)

    if is_object_type(type_):
        return _print_object(type_, schema, extras=extras)

    if is_input_type(type_):
        return _print_input_object(type_, schema, extras=extras)

    if is_interface_type(type_):
        return _print_interface(type_, schema, extras=extras)

    if is_union_type(type_):
        return print_union(type_, schema=schema, extras=extras)

    return original_print_type(type_)


def print_directives_on_schema(schema: BaseSchema, *, extras: PrintExtras) -> str:

    directives = (
        directive
        for directive in schema.schema_directives
        if any(
            location in [Location.SCHEMA]
            for location in directive.__strawberry_directive__.locations  # type: ignore
        )
    )

    return "".join(
        (
            print_schema_directive(directive, schema=schema, extras=extras)
            for directive in directives
        )
    )


def _all_root_names_are_common_names(schema: BaseSchema) -> bool:
    query = schema.query._type_definition
    mutation = schema.mutation._type_definition if schema.mutation else None
    subscription = schema.subscription._type_definition if schema.subscription else None

    return (
        query.name == "Query"
        and (mutation is None or mutation.name == "Mutation")
        and (subscription is None or subscription.name == "Subscription")
    )


def print_schema_definition(
    schema: BaseSchema, *, extras: PrintExtras
) -> Optional[str]:
    # TODO: add support for description

    if _all_root_names_are_common_names(schema) and not schema.schema_directives:
        return None

    query_type = schema.query._type_definition
    operation_types = [f"  query: {query_type.name}"]

    if schema.mutation:
        mutation_type = schema.mutation._type_definition
        operation_types.append(f"  mutation: {mutation_type.name}")

    if schema.subscription:
        subscription_type = schema.subscription._type_definition
        operation_types.append(f"  subscription: {subscription_type.name}")

    directives = print_directives_on_schema(schema, extras=extras)

    return f"schema{directives} {{\n" + "\n".join(operation_types) + "\n}"


def print_schema(schema: BaseSchema) -> str:
    graphql_core_schema = schema._schema  # type: ignore
    extras = PrintExtras()

    directives = filter(
        lambda n: not is_specified_directive(n), graphql_core_schema.directives
    )
    type_map = graphql_core_schema.type_map
    types = filter(is_defined_type, map(type_map.get, sorted(type_map)))

    types_printed = [_print_type(type_, schema, extras=extras) for type_ in types]
    schema_definition = print_schema_definition(schema, extras=extras)

    directives = filter(
        None,
        [
            print_directive_definition(directive, schema=schema)
            for directive in directives
        ],
    )

    return "\n\n".join(
        chain(
            sorted(extras.directives),
            filter(None, [schema_definition]),
            directives,
            types_printed,
            (
                _print_type(
                    schema.schema_converter.from_type(type_), schema, extras=extras
                )
                for type_ in extras.types
            ),
        )
    )
