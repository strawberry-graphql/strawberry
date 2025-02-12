from __future__ import annotations

import dataclasses
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)

from graphql import GraphQLObjectType, GraphQLSchema, is_union_type
from graphql.language.printer import print_ast
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
)
from graphql.utilities.print_schema import print_type as original_print_type

from strawberry.schema_directive import Location, StrawberrySchemaDirective
from strawberry.types.base import (
    StrawberryContainer,
    StrawberryObjectDefinition,
    has_object_definition,
)
from strawberry.types.enum import EnumDefinition
from strawberry.types.scalar import ScalarWrapper
from strawberry.types.unset import UNSET

from .ast_from_value import ast_from_value

if TYPE_CHECKING:
    from graphql import (
        GraphQLArgument,
        GraphQLEnumType,
        GraphQLEnumValue,
        GraphQLScalarType,
        GraphQLUnionType,
    )
    from graphql.type.directives import GraphQLDirective

    from strawberry.schema import BaseSchema
    from strawberry.types.field import StrawberryField


_T = TypeVar("_T")


@dataclasses.dataclass
class PrintExtras:
    directives: set[str] = dataclasses.field(default_factory=set)
    types: set[type] = dataclasses.field(default_factory=set)


@overload
def _serialize_dataclasses(
    value: dict[_T, object],
    *,
    name_converter: Callable[[str], str] | None = None,
) -> dict[_T, object]: ...


@overload
def _serialize_dataclasses(
    value: Union[list[object], tuple[object]],
    *,
    name_converter: Callable[[str], str] | None = None,
) -> list[object]: ...


@overload
def _serialize_dataclasses(
    value: object,
    *,
    name_converter: Callable[[str], str] | None = None,
) -> object: ...


def _serialize_dataclasses(
    value,
    *,
    name_converter: Callable[[str], str] | None = None,
):
    if name_converter is None:
        name_converter = lambda x: x  # noqa: E731

    if dataclasses.is_dataclass(value):
        return {
            name_converter(k): v
            for k, v in dataclasses.asdict(value).items()  # type: ignore
            if v is not UNSET
        }
    if isinstance(value, (list, tuple)):
        return [_serialize_dataclasses(v, name_converter=name_converter) for v in value]
    if isinstance(value, dict):
        return {
            name_converter(k): _serialize_dataclasses(v, name_converter=name_converter)
            for k, v in value.items()
        }

    return value


def print_schema_directive_params(
    directive: GraphQLDirective,
    values: dict[str, Any],
    *,
    schema: BaseSchema,
) -> str:
    params = []
    for name, arg in directive.args.items():
        value = values.get(name, arg.default_value)
        if value is UNSET:
            value = None
        else:
            ast = ast_from_value(
                _serialize_dataclasses(
                    value,
                    name_converter=schema.config.name_converter.apply_naming_config,
                ),
                arg.type,
            )
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
    gql_directive = schema_converter.from_schema_directive(directive.__class__)
    params = print_schema_directive_params(
        gql_directive,
        {
            schema.config.name_converter.get_graphql_name(f): getattr(
                directive, f.python_name or f.name, UNSET
            )
            for f in strawberry_directive.fields
        },
        schema=schema,
    )

    printed_directive = print_directive(gql_directive, schema=schema)

    if printed_directive is not None:
        extras.directives.add(printed_directive)

        for field in strawberry_directive.fields:
            f_type = field.type

            while isinstance(f_type, StrawberryContainer):
                f_type = f_type.of_type

            if has_object_definition(f_type):
                extras.types.add(cast(type, f_type))

            if hasattr(f_type, "_scalar_definition"):
                extras.types.add(cast(type, f_type))

            if isinstance(f_type, EnumDefinition):
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
        print_schema_directive(directive, schema=schema, extras=extras)
        for directive in directives
    )


def print_argument_directives(
    argument: GraphQLArgument, *, schema: BaseSchema, extras: PrintExtras
) -> str:
    strawberry_type = argument.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    return "".join(
        print_schema_directive(directive, schema=schema, extras=extras)
        for directive in directives
    )


def print_args(
    args: dict[str, GraphQLArgument],
    indentation: str = "",
    *,
    schema: BaseSchema,
    extras: PrintExtras,
) -> str:
    if not args:
        return ""

    # If every arg does not have a description, print them on one line.
    if not any(arg.description for arg in args.values()):
        return (
            "("
            + ", ".join(
                (
                    f"{print_input_value(name, arg)}"
                    f"{print_argument_directives(arg, schema=schema, extras=extras)}"
                )
                for name, arg in args.items()
            )
            + ")"
        )

    return (
        "(\n"
        + "\n".join(
            print_description(arg, f"  {indentation}", not i)
            + f"  {indentation}"
            + print_input_value(name, arg)
            + print_argument_directives(arg, schema=schema, extras=extras)
            for i, (name, arg) in enumerate(args.items())
        )
        + f"\n{indentation})"
    )


def print_fields(
    type_: GraphQLObjectType,
    schema: BaseSchema,
    *,
    extras: PrintExtras,
) -> str:
    from strawberry.schema.schema_converter import GraphQLCoreConverter

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
    # TODO: refactor this
    strawberry_type = type_.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    printed_directives = "".join(
        print_schema_directive(directive, schema=schema, extras=extras)
        for directive in directives
    )

    return (
        print_description(type_)
        + f"scalar {type_.name}"
        + print_specified_by_url(type_)
        + printed_directives
    ).strip()


def print_enum_value(
    name: str,
    value: GraphQLEnumValue,
    first_in_block: bool,
    *,
    schema: BaseSchema,
    extras: PrintExtras,
) -> str:
    strawberry_type = value.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    printed_directives = "".join(
        print_schema_directive(directive, schema=schema, extras=extras)
        for directive in directives
    )

    return (
        print_description(value, "  ", first_in_block)
        + f"  {name}"
        + print_deprecated(value.deprecation_reason)
        + printed_directives
    )


def print_enum(
    type_: GraphQLEnumType, *, schema: BaseSchema, extras: PrintExtras
) -> str:
    strawberry_type = type_.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    printed_directives = "".join(
        print_schema_directive(directive, schema=schema, extras=extras)
        for directive in directives
    )

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


def print_extends(type_: GraphQLObjectType, schema: BaseSchema) -> str:
    from strawberry.schema.schema_converter import GraphQLCoreConverter

    strawberry_type = cast(
        Optional[StrawberryObjectDefinition],
        type_.extensions
        and type_.extensions.get(GraphQLCoreConverter.DEFINITION_BACKREF),
    )

    if strawberry_type and strawberry_type.extend:
        return "extend "

    return ""


def print_type_directives(
    type_: GraphQLObjectType, schema: BaseSchema, *, extras: PrintExtras
) -> str:
    from strawberry.schema.schema_converter import GraphQLCoreConverter

    strawberry_type = cast(
        Optional[StrawberryObjectDefinition],
        type_.extensions
        and type_.extensions.get(GraphQLCoreConverter.DEFINITION_BACKREF),
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
            for location in directive.__strawberry_directive__.locations  # type: ignore[attr-defined]
        )
    )

    return "".join(
        print_schema_directive(directive, schema=schema, extras=extras)
        for directive in directives
    )


def _print_object(type_: Any, schema: BaseSchema, *, extras: PrintExtras) -> str:
    return (
        print_description(type_)
        + print_extends(type_, schema)
        + f"type {type_.name}"
        + print_implemented_interfaces(type_)
        + print_type_directives(type_, schema, extras=extras)
        + print_fields(type_, schema, extras=extras)
    )


def _print_interface(type_: Any, schema: BaseSchema, *, extras: PrintExtras) -> str:
    return (
        print_description(type_)
        + print_extends(type_, schema)
        + f"interface {type_.name}"
        + print_implemented_interfaces(type_)
        + print_type_directives(type_, schema, extras=extras)
        + print_fields(type_, schema, extras=extras)
    )


def print_input_value(name: str, arg: GraphQLArgument) -> str:
    default_ast = ast_from_value(arg.default_value, arg.type)
    arg_decl = f"{name}: {arg.type}"
    if default_ast:
        arg_decl += f" = {print_ast(default_ast)}"
    return arg_decl + print_deprecated(arg.deprecation_reason)


def _print_input_object(type_: Any, schema: BaseSchema, *, extras: PrintExtras) -> str:
    from strawberry.schema.schema_converter import GraphQLCoreConverter

    fields = []
    for i, (name, field) in enumerate(type_.fields.items()):
        strawberry_field = field.extensions and field.extensions.get(
            GraphQLCoreConverter.DEFINITION_BACKREF
        )

        fields.append(
            print_description(field, "  ", not i)
            + "  "
            + print_input_value(name, field)
            + print_field_directives(strawberry_field, schema=schema, extras=extras)
        )

    return (
        print_description(type_)
        + f"input {type_.name}"
        + print_type_directives(type_, schema, extras=extras)
        + print_block(fields)
    )


def print_union(
    type_: GraphQLUnionType, *, schema: BaseSchema, extras: PrintExtras
) -> str:
    strawberry_type = type_.extensions.get("strawberry-definition")
    directives = strawberry_type.directives if strawberry_type else []

    printed_directives = "".join(
        print_schema_directive(directive, schema=schema, extras=extras)
        for directive in directives
    )

    types = type_.types
    possible_types = " = " + " | ".join(t.name for t in types) if types else ""
    return (
        print_description(type_)
        + f"union {type_.name}{printed_directives}"
        + possible_types
    )


def _print_type(type_: Any, schema: BaseSchema, *, extras: PrintExtras) -> str:
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


def print_schema_directives(schema: BaseSchema, *, extras: PrintExtras) -> str:
    directives = (
        directive
        for directive in schema.schema_directives
        if any(
            location in [Location.SCHEMA]
            for location in directive.__strawberry_directive__.locations  # type: ignore
        )
    )

    return "".join(
        print_schema_directive(directive, schema=schema, extras=extras)
        for directive in directives
    )


def _all_root_names_are_common_names(schema: BaseSchema) -> bool:
    query = schema.query.__strawberry_definition__
    mutation = schema.mutation.__strawberry_definition__ if schema.mutation else None
    subscription = (
        schema.subscription.__strawberry_definition__ if schema.subscription else None
    )

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

    query_type = schema.query.__strawberry_definition__
    operation_types = [f"  query: {query_type.name}"]

    if schema.mutation:
        mutation_type = schema.mutation.__strawberry_definition__
        operation_types.append(f"  mutation: {mutation_type.name}")

    if schema.subscription:
        subscription_type = schema.subscription.__strawberry_definition__
        operation_types.append(f"  subscription: {subscription_type.name}")

    directives = print_schema_directives(schema, extras=extras)

    return f"schema{directives} {{\n" + "\n".join(operation_types) + "\n}"


def print_directive(
    directive: GraphQLDirective, *, schema: BaseSchema
) -> Optional[str]:
    strawberry_directive = directive.extensions["strawberry-definition"]

    if (
        isinstance(strawberry_directive, StrawberrySchemaDirective)
        and not strawberry_directive.print_definition
    ):
        return None

    return (
        print_description(directive)
        + f"directive @{directive.name}"
        # TODO: add support for directives on arguments directives
        + print_args(directive.args, schema=schema, extras=PrintExtras())
        + (" repeatable" if directive.is_repeatable else "")
        + " on "
        + " | ".join(location.name for location in directive.locations)
    )


def is_builtin_directive(directive: GraphQLDirective) -> bool:
    # this allows to force print the builtin directives if there's a
    # directive that was implemented using the schema_directive

    if is_specified_directive(directive):
        strawberry_definition = directive.extensions.get("strawberry-definition")

        return strawberry_definition is None

    return False


def print_schema(schema: BaseSchema) -> str:
    graphql_core_schema = cast(
        GraphQLSchema,
        schema._schema,  # type: ignore
    )
    extras = PrintExtras()

    filtered_directives = [
        directive
        for directive in graphql_core_schema.directives
        if not is_builtin_directive(directive)
    ]

    type_map = graphql_core_schema.type_map
    types = [
        type_
        for type_name in sorted(type_map)
        if is_defined_type(type_ := type_map[type_name])
    ]

    types_printed = [_print_type(type_, schema, extras=extras) for type_ in types]
    schema_definition = print_schema_definition(schema, extras=extras)

    directives = [
        printed_directive
        for directive in filtered_directives
        if (printed_directive := print_directive(directive, schema=schema)) is not None
    ]

    def _name_getter(type_: Any) -> str:
        if hasattr(type_, "name"):
            return type_.name
        if isinstance(type_, ScalarWrapper):
            return type_._scalar_definition.name
        return type_.__name__

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
                # Make sure extra types are ordered for predictive printing
                for type_ in sorted(extras.types, key=_name_getter)
            ),
        )
    )


__all__ = ["print_schema"]
