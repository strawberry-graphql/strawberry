from __future__ import annotations

from typing import TYPE_CHECKING, Any
from weakref import WeakKeyDictionary

from graphql import get_argument_values

from strawberry.extensions import SchemaExtension
from strawberry.types.arguments import convert_arguments
from strawberry.types.base import StrawberryContainer, has_object_definition
from strawberry.types.lazy_type import LazyType
from strawberry.utils.await_maybe import await_maybe

if TYPE_CHECKING:
    from collections.abc import Callable

    from graphql import DirectiveNode, GraphQLResolveInfo

    from strawberry.directive import StrawberryDirective, StrawberryDirectiveResolver
    from strawberry.schema.schema import Schema
    from strawberry.types.base import StrawberryType
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
    if not hasattr(variable_values, "coerced"):
        # Strawberry exposes a plain dict, while graphql-core expects its
        # VariableValues container when coercing arguments.
        from graphql.execution import values as execution_values

        variable_values_type = vars(execution_values)["VariableValues"]
        variable_values = variable_values_type({}, variable_values)

    resolver = strawberry_directive.resolver
    info_parameter = resolver.info_parameter
    value_parameter = resolver.value_parameter

    # the info is only built when it can be used: by the resolver, or by input
    # types that build their own value
    strawberry_info = None
    if info_parameter or _has_input_object_arguments(strawberry_directive):
        field: StrawberryField = schema.get_field_for_type(  # type: ignore
            field_name=info.field_name,
            type_name=info.parent_type.name,
        )
        strawberry_info = schema.config.info_class(_raw_info=info, _field=field)

    arguments = get_argument_values(directive_definition, directive, variable_values)
    arguments = convert_arguments(
        arguments,
        strawberry_directive.arguments,
        scalar_registry=schema.schema_converter.scalar_registry,
        config=schema.config,
        info=strawberry_info,
    )

    if info_parameter:
        arguments[info_parameter.name] = strawberry_info
    if value_parameter:
        arguments[value_parameter.name] = value
    return strawberry_directive, arguments


# the answer never changes for a directive, and checking it on every use of the
# directive would slow down queries that use many directives
_input_object_arguments: WeakKeyDictionary[StrawberryDirectiveResolver[Any], bool] = (
    WeakKeyDictionary()
)


def _has_input_object_arguments(directive: StrawberryDirective) -> bool:
    if (cached := _input_object_arguments.get(directive.resolver)) is not None:
        return cached

    result = any(_is_input_object(argument.type) for argument in directive.arguments)
    _input_object_arguments[directive.resolver] = result

    return result


def _is_input_object(type_: StrawberryType | type) -> bool:
    while isinstance(type_, StrawberryContainer):
        type_ = type_.of_type

    if isinstance(type_, LazyType):
        return _is_input_object(type_.resolve_type())

    return has_object_definition(type_)


__all__ = ["DirectivesExtension", "DirectivesExtensionSync"]
