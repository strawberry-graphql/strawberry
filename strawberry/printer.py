from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Dict, Optional, cast

from graphql.type import (
    is_enum_type,
    is_input_type,
    is_object_type,
    is_scalar_type,
    is_specified_directive,
)
from graphql.utilities.print_schema import (
    is_defined_type,
    print_args,
    print_block,
    print_deprecated,
    print_description,
    print_directive,
    print_enum,
    print_implemented_interfaces,
    print_input_value,
    print_scalar,
    print_schema_definition,
    print_type as original_print_type,
)

from strawberry.field import StrawberryField
from strawberry.schema_directive import Location, StrawberrySchemaDirective
from strawberry.types.types import TypeDefinition


if TYPE_CHECKING:
    from strawberry.schema import BaseSchema


def print_schema_directive_params(params: Dict) -> str:
    if not params:
        return ""

    return "(" + ", ".join(f'{name}: "{value}"' for name, value in params.items()) + ")"


def print_schema_directive(
    directive: StrawberrySchemaDirective, schema: BaseSchema
) -> str:
    params = directive.instance.__dict__ if directive.instance else {}

    directive_name = schema.config.name_converter.from_directive(directive)

    return f" @{directive_name}{print_schema_directive_params(params)}"


def print_field_directives(field: Optional[StrawberryField], schema: BaseSchema) -> str:
    if not field:
        return ""

    directives = (
        directive
        for directive in field.directives
        if any(
            location in [Location.FIELD_DEFINITION, Location.INPUT_FIELD_DEFINITION]
            for location in directive.locations
        )
    )

    return "".join(
        (print_schema_directive(directive, schema=schema) for directive in directives)
    )


def print_fields(type_, schema: BaseSchema) -> str:
    strawberry_type = cast(TypeDefinition, schema.get_type_by_name(type_.name))

    fields = []

    for i, (name, field) in enumerate(type_.fields.items()):
        python_name = field.extensions and field.extensions.get("python_name")

        strawberry_field = (
            strawberry_type.get_field(python_name)
            if strawberry_type and python_name
            else None
        )

        args = print_args(field.args, "  ") if hasattr(field, "args") else ""

        fields.append(
            print_description(field, "  ", not i)
            + f"  {name}"
            + args
            + f": {field.type}"
            + print_field_directives(strawberry_field, schema=schema)
            + print_deprecated(field.deprecation_reason)
        )

    return print_block(fields)


def print_extends(type_, schema: BaseSchema):
    strawberry_type = cast(TypeDefinition, schema.get_type_by_name(type_.name))

    if strawberry_type and strawberry_type.extend:
        return "extend "

    return ""


def print_type_directives(type_, schema: BaseSchema) -> str:
    strawberry_type = cast(TypeDefinition, schema.get_type_by_name(type_.name))

    if not strawberry_type:
        return ""

    allowed_locations = (
        [Location.INPUT_OBJECT] if strawberry_type.is_input else [Location.OBJECT]
    )

    directives = (
        directive
        for directive in strawberry_type.directives or []
        if any(location in allowed_locations for location in directive.locations)
    )

    return "".join(
        (print_schema_directive(directive, schema=schema) for directive in directives)
    )


def _print_object(type_, schema: BaseSchema) -> str:
    return (
        print_description(type_)
        + print_extends(type_, schema)
        + f"type {type_.name}"
        + print_implemented_interfaces(type_)
        + print_type_directives(type_, schema)
        + print_fields(type_, schema)
    )


def _print_input_object(type_, schema: BaseSchema) -> str:
    fields = [
        print_description(field, "  ", not i) + "  " + print_input_value(name, field)
        for i, (name, field) in enumerate(type_.fields.items())
    ]
    return (
        print_description(type_)
        + f"input {type_.name}"
        + print_type_directives(type_, schema)
        + print_block(fields)
    )


def _print_type(type_, schema: BaseSchema) -> str:
    # prevents us from trying to print a scalar as an input type
    if is_scalar_type(type_):
        return print_scalar(type_)

    if is_enum_type(type_):
        return print_enum(type_)

    if is_object_type(type_):
        return _print_object(type_, schema)

    if is_input_type(type_):
        return _print_input_object(type_, schema)

    return original_print_type(type_)


def print_schema(schema: BaseSchema) -> str:
    graphql_core_schema = schema._schema  # type: ignore

    directives = filter(
        lambda n: not is_specified_directive(n), graphql_core_schema.directives
    )
    type_map = graphql_core_schema.type_map

    types = filter(is_defined_type, map(type_map.get, sorted(type_map)))

    return "\n\n".join(
        chain(
            filter(None, [print_schema_definition(graphql_core_schema)]),
            (print_directive(directive) for directive in directives),
            (_print_type(type_, schema) for type_ in types),
        )
    )
