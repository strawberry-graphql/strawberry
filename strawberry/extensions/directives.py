from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple

from graphql import OperationDefinitionNode

from strawberry.extensions import SchemaExtension
from strawberry.types import Info
from strawberry.types.nodes import convert_arguments
from strawberry.utils.await_maybe import AsyncIteratorOrIterator, await_maybe

if TYPE_CHECKING:
    from graphql import DirectiveNode, GraphQLResolveInfo

    from strawberry.directive import StrawberryDirective
    from strawberry.field import StrawberryField
    from strawberry.schema.schema import Schema
    from strawberry.types import ExecutionContext
    from strawberry.utils.await_maybe import AwaitableOrValue


SPECIFIED_DIRECTIVES = {"include", "skip"}


class CurrentDefinitionMixin:
    execution_context: ExecutionContext

    @property
    def current_definition(self) -> OperationDefinitionNode:
        assert self.execution_context.graphql_document

        if self.execution_context.operation_name:
            for definition in self.execution_context.graphql_document.definitions:
                if isinstance(definition, OperationDefinitionNode) and (
                    definition.name
                    and definition.name.value == self.execution_context.operation_name
                ):
                    return definition

            raise ValueError(
                f"Operation {self.execution_context.operation_name} not found"
            )

        definition = next(
            (
                definition
                for definition in self.execution_context.graphql_document.definitions
                if isinstance(definition, OperationDefinitionNode)
            ),
            None,
        )

        if definition is None:
            raise ValueError("No operation found")

        return definition


class DirectivesExtension(SchemaExtension):
    async def _handle_directives(
        self, value: Any, directives: List[DirectiveNode], info: Any = None
    ) -> Any:
        for directive in directives:
            if directive.name.value in SPECIFIED_DIRECTIVES:
                continue

            strawberry_directive, arguments = process_directive(
                directive=directive,
                value=value,
                info=info,
                schema=self.execution_context.schema,
            )

            value = await await_maybe(strawberry_directive.resolver(**arguments))

        return value

    async def on_execute(self) -> AsyncIteratorOrIterator[None]:
        yield

        value = self.execution_context.result.data

        # TODO: info is none here, but it's probably fine

        self.execution_context.result.data = await self._handle_directives(
            value, self.current_definition.directives
        )

    async def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        value = await await_maybe(_next(root, info, *args, **kwargs))

        return await self._handle_directives(
            value, info.field_nodes[0].directives, info
        )


class DirectivesExtensionSync(SchemaExtension, CurrentDefinitionMixin):
    def _handle_directives(
        self, value: Any, directives: List[DirectiveNode], info: Any = None
    ) -> Any:
        for directive in directives:
            if directive.name.value in SPECIFIED_DIRECTIVES:
                continue

            strawberry_directive, arguments = process_directive(
                directive=directive,
                value=value,
                info=info,
                schema=self.execution_context.schema,
            )

            # TODO: was this a bug? - add test with multiple directives
            value = strawberry_directive.resolver(**arguments)

        return value

    def on_execute(self) -> AsyncIteratorOrIterator[None]:
        yield

        value = self.execution_context.result.data

        # TODO: info is none here, but it's probably fine

        self.execution_context.result.data = self._handle_directives(
            value, self.current_definition.directives
        )

    def resolve(
        self,
        _next: Callable,
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[Any]:
        value = _next(root, info, *args, **kwargs)

        return self._handle_directives(value, info.field_nodes[0].directives, info)


def process_directive(
    directive: DirectiveNode,
    value: Any,
    info: GraphQLResolveInfo,
    schema: Schema,
) -> Tuple[StrawberryDirective[Any], Dict[str, Any]]:
    """Get a `StrawberryDirective` from ``directive` and prepare its arguments."""
    directive_name = directive.name.value

    strawberry_directive = schema.get_directive_by_name(directive_name)
    assert strawberry_directive is not None, f"Directive {directive_name} not found"

    arguments = convert_arguments(info=info, nodes=directive.arguments)
    resolver = strawberry_directive.resolver

    info_parameter = resolver.info_parameter
    value_parameter = resolver.value_parameter
    if info_parameter:
        field: StrawberryField = schema.get_field_for_type(  # type: ignore
            field_name=info.field_name,
            type_name=info.parent_type.name,
        )
        arguments[info_parameter.name] = Info(_raw_info=info, _field=field)
    if value_parameter:
        arguments[value_parameter.name] = value
    return strawberry_directive, arguments
