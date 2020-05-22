import dataclasses
from itertools import chain
from typing import Callable

from graphql.type import (
    GraphQLDirective,
    GraphQLNamedType,
    GraphQLSchema,
    is_object_type,
    is_specified_directive,
)
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

from .type_registry import get_strawberry_type_for_graphql_type


def print_federation_field_directive(field, metadata):
    out = ""

    if metadata and "federation" in metadata:
        federation = metadata["federation"]

        provides = federation.get("provides", "")
        requires = federation.get("requires", "")
        external = federation.get("external", False)

        if provides:
            out += f' @provides(fields: "{provides}")'

        if requires:
            out += f' @requires(fields: "{requires}")'

        if external:
            out += " @external"

    return out


def print_fields(type_) -> str:
    strawberry_type = get_strawberry_type_for_graphql_type(type_)
    strawberry_fields = dataclasses.fields(strawberry_type) if strawberry_type else []

    def _get_metadata(field_name):
        return next(
            (
                f.metadata
                for f in strawberry_fields
                if (getattr(f, "field_name", None) or f.name) == field_name
            ),
            None,
        )

    fields = [
        print_description(field, "  ", not i)
        + f"  {name}"
        + print_args(field.args, "  ")
        + f": {field.type}"
        + print_federation_field_directive(field, _get_metadata(name))
        + print_deprecated(field)
        for i, (name, field) in enumerate(type_.fields.items())
    ]
    return print_block(fields)


def print_federation_key_directive(type_):
    strawberry_type = get_strawberry_type_for_graphql_type(type_)

    if not strawberry_type:
        return ""

    keys = getattr(strawberry_type, "_federation_keys", [])

    parts = []

    for key in keys:
        parts.append(f'@key(fields: "{key}")')

    if not parts:
        return ""

    return " " + " ".join(parts)


def print_extends(type_):
    strawberry_type = get_strawberry_type_for_graphql_type(type_)

    if strawberry_type and getattr(strawberry_type, "_federation_extend", False):
        return "extend "

    return ""


def print_object(type_) -> str:
    return (
        print_description(type_)
        + print_extends(type_)
        + f"type {type_.name}"
        + print_federation_key_directive(type_)
        + print_implemented_interfaces(type_)
        + print_fields(type_)
    )


def print_type(field) -> str:
    """Returns a string representation of a strawberry type"""

    if hasattr(field, "graphql_type"):
        field = field.graphql_type

    if is_object_type(field):
        return print_object(field)

    return original_print_type(field)


def print_filtered_schema(
    schema: GraphQLSchema,
    directive_filter: Callable[[GraphQLDirective], bool],
    type_filter: Callable[[GraphQLNamedType], bool],
) -> str:
    directives = filter(directive_filter, schema.directives)
    type_map = schema.type_map

    types = filter(type_filter, map(type_map.get, sorted(type_map)))  # type: ignore

    return "\n\n".join(
        chain(
            filter(None, [print_schema_definition(schema)]),
            (print_directive(directive) for directive in directives),
            (print_type(type_) for type_ in types),  # type: ignore
        )
    )


def print_schema(schema: GraphQLSchema) -> str:
    return print_filtered_schema(
        schema, lambda n: not is_specified_directive(n), is_defined_type
    )
