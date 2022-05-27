from __future__ import annotations

import dataclasses
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from graphql.language.printer import print_ast
from graphql.type import (
    is_enum_type,
    is_input_type,
    is_object_type,
    is_scalar_type,
    is_specified_directive,
)
from graphql.type.directives import GraphQLDirective
from graphql.utilities.ast_from_value import ast_from_value
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
from strawberry.type import StrawberryContainer
from strawberry.types.types import TypeDefinition
from strawberry.unset import UNSET


if TYPE_CHECKING:
    from strawberry.schema import BaseSchema


_T = TypeVar("_T")


@dataclasses.dataclass
class PrintExtras:
    directives: Set[str] = dataclasses.field(default_factory=set)
    types: Set[type] = dataclasses.field(default_factory=set)


@overload
def _serialize_dataclasses(value: Dict[_T, object]) -> Dict[_T, object]:
    ...


@overload
def _serialize_dataclasses(value: Union[List[object], Tuple[object]]) -> List[object]:
    ...


@overload
def _serialize_dataclasses(value: object) -> object:
    ...


def _serialize_dataclasses(value):
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if isinstance(value, (list, tuple)):
        return [_serialize_dataclasses(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_dataclasses(v) for k, v in value.items()}

    return value


def print_schema_directive_params(
    directive: GraphQLDirective, values: Dict[str, Any]
) -> str:
    params = []
    for name, arg in directive.args.items():
        value = values.get(name, arg.default_value)
        if value is UNSET:
            value = None
        else:
            ast = ast_from_value(_serialize_dataclasses(value), arg.type)
            value = ast and f"{name}: {print_ast(ast)}"

        if value:
            params.append(value)

    if not params:
        return ""

    return "(" + ", ".join(params) + ")"


def print_schema_directive(
    directive: Any, schema: BaseSchema, *, extras: PrintExtras
) -> str:
    strawberry_directive = cast(
        StrawberrySchemaDirective, directive.__class__.__strawberry_directive__
    )
    schema_converter = schema.schema_converter
    gql_directive = schema_converter.from_schema_directive(directive)
    params = print_schema_directive_params(
        gql_directive,
        {
            schema.config.name_converter.get_graphql_name(f): getattr(
                directive, f.python_name or f.name, UNSET
            )
            for f in strawberry_directive.fields
        },
    )

    extras.directives.add(print_directive(gql_directive))
    for field in strawberry_directive.fields:
        f_type = field.type
        while isinstance(f_type, StrawberryContainer):
            f_type = f_type.of_type

        if hasattr(f_type, "_type_definition"):
            extras.types.add(cast(type, f_type))

    return f" @{gql_directive.name}{params}"


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


def print_fields(type_, schema: BaseSchema, *, extras: PrintExtras) -> str:
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
            + print_field_directives(strawberry_field, schema=schema, extras=extras)
            + print_deprecated(field.deprecation_reason)
        )

    return print_block(fields)


def print_extends(type_, schema: BaseSchema):
    strawberry_type = cast(TypeDefinition, schema.get_type_by_name(type_.name))

    if strawberry_type and strawberry_type.extend:
        return "extend "

    return ""


def print_type_directives(type_, schema: BaseSchema, *, extras: PrintExtras) -> str:
    strawberry_type = cast(TypeDefinition, schema.get_type_by_name(type_.name))

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
            for location in directive.__strawberry_directive__.locations  # type: ignore
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


def _print_type(type_, schema: BaseSchema, *, extras: PrintExtras) -> str:
    # prevents us from trying to print a scalar as an input type
    if is_scalar_type(type_):
        return print_scalar(type_)

    if is_enum_type(type_):
        return print_enum(type_)

    if is_object_type(type_):
        return _print_object(type_, schema, extras=extras)

    if is_input_type(type_):
        return _print_input_object(type_, schema, extras=extras)

    return original_print_type(type_)


def print_schema(schema: BaseSchema) -> str:
    graphql_core_schema = schema._schema  # type: ignore
    extras = PrintExtras()

    directives = filter(
        lambda n: not is_specified_directive(n), graphql_core_schema.directives
    )
    type_map = graphql_core_schema.type_map
    types = filter(is_defined_type, map(type_map.get, sorted(type_map)))

    types_printed = [_print_type(type_, schema, extras=extras) for type_ in types]

    return "\n\n".join(
        chain(
            filter(None, [print_schema_definition(graphql_core_schema)]),
            sorted(extras.directives),
            (print_directive(directive) for directive in directives),
            types_printed,
            (
                _print_type(
                    schema.schema_converter.from_type(type_), schema, extras=extras
                )
                for type_ in extras.types
            ),
        )
    )
