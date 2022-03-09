from typing import TYPE_CHECKING, Any, Dict, Tuple

from graphql import DirectiveNode

from strawberry.directive import StrawberryDirective
from strawberry.extensions import Extension
from strawberry.types import Info
from strawberry.utils.await_maybe import AwaitableOrValue, await_maybe


if TYPE_CHECKING:
    from strawberry.schema.schema import Schema


SPECIFIED_DIRECTIVES = {"include", "skip"}


class DirectivesExtension(Extension):
    async def resolve(
        self, _next, root, info: Info, *args, **kwargs
    ) -> AwaitableOrValue[Any]:
        value = await await_maybe(_next(root, info, *args, **kwargs))

        for directive in info.field_nodes[0].directives:
            if directive.name.value in SPECIFIED_DIRECTIVES:
                continue
            strawberry_directive, arguments = process_directive(
                directive, value, root, info
            )
            value = await await_maybe(strawberry_directive.resolver(**arguments))

        return value


class DirectivesExtensionSync(Extension):
    def resolve(self, _next, root, info, *args, **kwargs) -> AwaitableOrValue[Any]:
        value = _next(root, info, *args, **kwargs)

        for directive in info.field_nodes[0].directives:
            if directive.name.value in SPECIFIED_DIRECTIVES:
                continue
            strawberry_directive, arguments = process_directive(
                directive, value, root, info
            )
            value = strawberry_directive.resolver(**arguments)

        return value


def process_directive(
    directive: DirectiveNode,
    value: Any,
    root: Any,
    info: Info,
) -> Tuple[StrawberryDirective, Dict[str, Any]]:
    """Get a `StrawberryDirective` from ``directive` and prepare its arguments."""
    directive_name = directive.name.value
    schema: Schema = info.schema._strawberry_schema  # type: ignore

    strawberry_directive = schema.get_directive_by_name(directive_name)
    assert strawberry_directive is not None, f"Directive {directive_name} not found"

    arguments = {
        argument.name.value: argument.value.value  # type: ignore
        for argument in directive.arguments
    }
    resolver = strawberry_directive.resolver

    info_parameter = resolver.info_parameter
    root_parameter = resolver.root_parameter
    value_parameter = resolver.value_parameter
    if info_parameter:
        arguments[info_parameter.name] = info
    if root_parameter:
        arguments[root_parameter.name] = root
    if value_parameter:
        arguments[value_parameter.name] = value
    return strawberry_directive, arguments
