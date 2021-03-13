from itertools import chain
from typing import Optional, cast

from graphql.type import is_object_type, is_specified_directive
from graphql.utilities.print_schema import (
    is_defined_type,
    print_args,
    print_block,
    print_deprecated,
    print_description,
    print_directive,
    print_implemented_interfaces,
    print_schema_definition,
    print_type as original_print_type,
)

from strawberry.field import StrawberryField
from strawberry.types.types import TypeDefinition

from .schema import BaseSchema


def print_federation_field_directive(field: Optional[StrawberryField]) -> str:
    if not field:
        return ""

    out = ""

    if field.federation.provides:
        out += f' @provides(fields: "{field.federation.provides}")'

    if field.federation.requires:
        out += f' @requires(fields: "{field.federation.requires}")'

    if field.federation.external:
        out += " @external"

    return out


def print_fields(type_, schema: BaseSchema) -> str:
    strawberry_type = cast(TypeDefinition, schema.get_type_by_name(type_.name))

    fields = []

    for i, (name, field) in enumerate(type_.fields.items()):
        strawberry_field = strawberry_type.get_field(name) if strawberry_type else None

        fields.append(
            print_description(field, "  ", not i)
            + f"  {name}"
            + print_args(field.args, "  ")
            + f": {field.type}"
            + print_federation_field_directive(strawberry_field)
            + print_deprecated(field)
        )

    return print_block(fields)


def print_federation_key_directive(type_, schema: BaseSchema):
    strawberry_type = cast(TypeDefinition, schema.get_type_by_name(type_.name))

    if not strawberry_type:
        return ""

    keys = strawberry_type.federation.keys

    parts = []

    for key in keys:
        parts.append(f'@key(fields: "{key}")')

    if not parts:
        return ""

    return " " + " ".join(parts)


def print_extends(type_, schema: BaseSchema):
    strawberry_type = cast(TypeDefinition, schema.get_type_by_name(type_.name))

    if strawberry_type and strawberry_type.federation.extend:
        return "extend "

    return ""


def _print_object(type_, schema: BaseSchema) -> str:
    return (
        print_description(type_)
        + print_extends(type_, schema)
        + f"type {type_.name}"
        + print_federation_key_directive(type_, schema)
        + print_implemented_interfaces(type_)
        + print_fields(type_, schema)
    )


def _print_type(field, schema: BaseSchema) -> str:
    if is_object_type(field):
        return _print_object(field, schema)

    return original_print_type(field)


def print_schema(schema: BaseSchema) -> str:
    graphql_core_schema = schema._schema  # type: ignore

    directives = filter(
        lambda n: not is_specified_directive(n), graphql_core_schema.directives
    )
    type_map = graphql_core_schema.type_map

    types = filter(is_defined_type, map(type_map.get, sorted(type_map)))  # type: ignore

    return "\n\n".join(
        chain(
            filter(None, [print_schema_definition(graphql_core_schema)]),
            (print_directive(directive) for directive in directives),
            (_print_type(type_, schema) for type_ in types),  # type: ignore
        )
    )
