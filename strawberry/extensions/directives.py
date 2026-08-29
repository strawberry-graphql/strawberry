from __future__ import annotations

from typing import TYPE_CHECKING, Any

from graphql import get_argument_values

from strawberry.extensions import SchemaExtension
from strawberry.types.arguments import convert_arguments
from strawberry.utils import IS_GQL_33
from strawberry.utils.await_maybe import await_maybe

if TYPE_CHECKING:
    from collections.abc import Callable

    from graphql import DirectiveNode, GraphQLResolveInfo

    from strawberry.directive import StrawberryDirective
    from strawberry.schema.schema import Schema
    from strawberry.types.field import StrawberryField
    from strawberry.utils.await_maybe import AwaitableOrValue


SPECIFIED_DIRECTIVES = {"include", "skip"}


class DirectivesExtension(SchemaExtension):
    async def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        value = await await_maybe(_next(root, info, *args, **kwargs))

        nodes = list(info.field_nodes)

        for directive in nodes[0].directives or ():
            if directive.name.value in SPECIFIED_DIRECTIVES:
                continue
            strawberry_directive, arguments = process_directive(directive, value, info)
            value = await await_maybe(strawberry_directive.resolver(**arguments))

        return value


class DirectivesExtensionSync(SchemaExtension):
    def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        value = _next(root, info, *args, **kwargs)

        nodes = list(info.field_nodes)

        for directive in nodes[0].directives or ():
            if directive.name.value in SPECIFIED_DIRECTIVES:
                continue
            strawberry_directive, arguments = process_directive(directive, value, info)
            value = strawberry_directive.resolver(**arguments)

        return value


def process_directive(
    directive: DirectiveNode,
    value: Any,
    info: GraphQLResolveInfo,
) -> tuple[StrawberryDirective, dict[str, Any]]:
    """Get a `StrawberryDirective` from ``directive` and prepare its arguments."""
    directive_name = directive.name.value
    schema: Schema = info.schema._strawberry_schema  # type: ignore

    strawberry_directive = schema.get_directive_by_name(directive_name)
    assert strawberry_directive is not None, f"Directive {directive_name} not found"

    directive_definition = info.schema.get_directive(directive_name)
    assert directive_definition is not None, f"Directive {directive_name} not found"

    variable_values: Any = info.variable_values
    if IS_GQL_33 and not hasattr(variable_values, "coerced"):
        # Strawberry exposes a plain dict, while graphql-core 3.3 expects its
        # VariableValues container when coercing arguments.
        from graphql.execution import values as execution_values

        variable_values_type = vars(execution_values)["VariableValues"]
        variable_values = variable_values_type({}, variable_values)

    arguments = get_argument_values(directive_definition, directive, variable_values)
    arguments = convert_arguments(
        arguments,
        strawberry_directive.arguments,
        scalar_registry=schema.schema_converter.scalar_registry,
        config=schema.config,
    )
    resolver = strawberry_directive.resolver

    info_parameter = resolver.info_parameter
    value_parameter = resolver.value_parameter
    if info_parameter:
        field: StrawberryField = schema.get_field_for_type(  # type: ignore
            field_name=info.field_name,
            type_name=info.parent_type.name,
        )
        arguments[info_parameter.name] = schema.config.info_class(
            _raw_info=info, _field=field
        )
    if value_parameter:
        arguments[value_parameter.name] = value
    return strawberry_directive, arguments


__all__ = ["DirectivesExtension", "DirectivesExtensionSync"]
