from __future__ import annotations

from typing import TYPE_CHECKING, Any

from strawberry.extensions import SchemaExtension
from strawberry.types.nodes import convert_arguments
from strawberry.utils.await_maybe import await_maybe

if TYPE_CHECKING:
    from collections.abc import Callable

    from graphql import DirectiveNode

    from strawberry.directive import StrawberryDirective
    from strawberry.types.info import Info
    from strawberry.utils.await_maybe import AwaitableOrValue


SPECIFIED_DIRECTIVES = {"include", "skip"}


class DirectivesExtension(SchemaExtension):
    async def resolve(
        self,
        _next: Callable,
        root: Any,
        info: Info,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        value = await await_maybe(_next(root, info, *args, **kwargs))

        nodes = list(info._raw_info.field_nodes)

        for directive in nodes[0].directives:
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
        info: Info,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        value = _next(root, info, *args, **kwargs)

        nodes = list(info._raw_info.field_nodes)

        for directive in nodes[0].directives:
            if directive.name.value in SPECIFIED_DIRECTIVES:
                continue
            strawberry_directive, arguments = process_directive(directive, value, info)
            value = strawberry_directive.resolver(**arguments)

        return value


def process_directive(
    directive: DirectiveNode,
    value: Any,
    info: Info,
) -> tuple[StrawberryDirective, dict[str, Any]]:
    """Get a `StrawberryDirective` from ``directive` and prepare its arguments."""
    directive_name = directive.name.value

    strawberry_directive = info.schema.get_directive_by_name(directive_name)
    assert strawberry_directive is not None, f"Directive {directive_name} not found"

    arguments = convert_arguments(info=info._raw_info, nodes=directive.arguments)
    resolver = strawberry_directive.resolver

    if resolver.info_parameter:
        arguments[resolver.info_parameter.name] = info
    if resolver.value_parameter:
        arguments[resolver.value_parameter.name] = value
    return strawberry_directive, arguments


__all__ = ["DirectivesExtension", "DirectivesExtensionSync"]
