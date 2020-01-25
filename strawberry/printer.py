import dataclasses
from itertools import chain
from typing import Callable, Dict, List, Union

from graphql.language import print_ast
from graphql.language.block_string import print_block_string
from graphql.type import (
    DEFAULT_DEPRECATION_REASON,
    GraphQLArgument,
    GraphQLDirective,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    is_object_type,
    is_specified_directive,
)
from graphql.utilities.ast_from_value import ast_from_value
from graphql.utilities.print_schema import (
    is_defined_type,
    print_directive,
    print_schema_definition,
    print_type as original_print_type,
)


def print_description(
    def_: Union[GraphQLArgument, GraphQLDirective, GraphQLEnumValue, GraphQLNamedType],
    indentation="",
    first_in_block=True,
) -> str:
    description = def_.description
    if description is None:
        return ""

    prefer_multiple_lines = len(description) > 70
    block_string = print_block_string(description, "", prefer_multiple_lines)

    prefix = "\n" + indentation if indentation and not first_in_block else indentation

    return prefix + block_string.replace("\n", "\n" + indentation) + "\n"


def print_implemented_interfaces(
    type_: Union[GraphQLObjectType, GraphQLInterfaceType]
) -> str:
    interfaces = type_.interfaces
    return " implements " + " & ".join(i.name for i in interfaces) if interfaces else ""


def print_input_value(name: str, arg: GraphQLArgument) -> str:
    default_ast = ast_from_value(arg.default_value, arg.type)
    arg_decl = f"{name}: {arg.type}"
    if default_ast:
        arg_decl += f" = {print_ast(default_ast)}"
    return arg_decl


def print_args(args: Dict[str, GraphQLArgument], indentation="") -> str:
    if not args:
        return ""

    # If every arg does not have a description, print them on one line.
    if not any(arg.description for arg in args.values()):
        return (
            "("
            + ", ".join(print_input_value(name, arg) for name, arg in args.items())
            + ")"
        )

    return (
        "(\n"
        + "\n".join(
            print_description(arg, f"  {indentation}", not i)
            + f"  {indentation}"
            + print_input_value(name, arg)
            for i, (name, arg) in enumerate(args.items())
        )
        + f"\n{indentation})"
    )


def print_deprecated(field_or_enum_value: Union[GraphQLField, GraphQLEnumValue]) -> str:
    if not field_or_enum_value.is_deprecated:
        return ""
    reason = field_or_enum_value.deprecation_reason
    reason_ast = ast_from_value(reason, GraphQLString)
    if not reason_ast or reason == DEFAULT_DEPRECATION_REASON:
        return " @deprecated"
    return f" @deprecated(reason: {print_ast(reason_ast)})"


def print_block(items: List[str]) -> str:
    return " {\n" + "\n".join(items) + "\n}" if items else ""


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
    strawberry_type = getattr(type_, "_strawberry_type", None)
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
    strawberry_type = getattr(type_, "_strawberry_type", None)

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
    strawberry_type = getattr(type_, "_strawberry_type", None)

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
