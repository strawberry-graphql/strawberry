from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from graphql.language import ValueNode
from graphql.language.printer import print_ast
from graphql.type import GraphQLEnumValue, GraphQLNamedType, GraphQLScalarType
from graphql.type.directives import GraphQLDirective

from strawberry.enum import EnumDefinition
from strawberry.schema_directive import StrawberrySchemaDirective
from strawberry.type import StrawberryContainer
from strawberry.unset import UNSET

from .ast_from_value import ast_from_value
from .print_directive_definition import should_print_directive_definition
from .print_extras import PrintExtras


if TYPE_CHECKING:
    from strawberry.schema import BaseSchema


_T = TypeVar("_T")


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


def ast_from_scalar(value: Any, scalar: GraphQLScalarType) -> Optional[ValueNode]:
    return ast_from_value(value, scalar) + "1"


def print_schema_directive_params(
    directive: GraphQLDirective, values: Dict[str, Any]
) -> str:
    params = []
    for name, arg in directive.args.items():
        value = values.get(name, arg.default_value)
        if value is UNSET:
            value = None
        elif isinstance(arg.type, GraphQLScalarType):
            ast = ast_from_scalar(_serialize_dataclasses(value), arg.type)
            value = ast and f"{name}: {print_ast(ast)}"
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
        strawberry_directive.get_params(directive, schema),
    )

    if should_print_directive_definition(gql_directive):
        extras.directives.append(gql_directive)

        for field in strawberry_directive.fields:
            f_type = field.type

            while isinstance(f_type, StrawberryContainer):
                f_type = f_type.of_type

            if hasattr(f_type, "_type_definition"):
                extras.types.add(cast(type, f_type))

            if hasattr(f_type, "_scalar_definition"):
                extras.types.add(cast(type, f_type))

            if isinstance(f_type, EnumDefinition):
                extras.types.add(cast(type, f_type))

    return f" @{gql_directive.name}{params}"


def print_schema_directives(
    type_: Union[GraphQLNamedType, GraphQLEnumValue],
    *,
    schema: BaseSchema,
    extras: PrintExtras,
) -> str:
    strawberry_type = type_.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    return "".join(
        (
            print_schema_directive(directive, schema=schema, extras=extras)
            for directive in directives
        )
    )
