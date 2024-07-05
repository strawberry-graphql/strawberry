from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, Union

from graphql import (
    ExecutionResult as OriginalExecutionResult,
)
from graphql.execution import subscribe as original_subscribe

from strawberry.types import ExecutionResult
from strawberry.types.execution import ExecutionContext, ExecutionResultError

from .execute import ProccessErrors, _handle_execution_result, _parse_and_validate_async

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from graphql.execution.middleware import MiddlewareManager
    from graphql.type.schema import GraphQLSchema

    from ..extensions.runner import SchemaExtensionsRunner

SubscriptionResult: TypeAlias = AsyncGenerator[
    Union[ExecutionResultError, ExecutionResult], None
]


async def subscribe(
    schema: GraphQLSchema,
    execution_context: ExecutionContext,
    extensions_runner: SchemaExtensionsRunner,
    process_errors: ProccessErrors,
    middleware_manager: MiddlewareManager,
) -> SubscriptionResult:
    async with extensions_runner.operation():
        if initial_error := await _parse_and_validate_async(
            context=execution_context,
            extensions_runner=extensions_runner,
        ):
            initial_error.extensions = await extensions_runner.get_extensions_results(
                execution_context
            )
            yield await _handle_execution_result(
                execution_context, initial_error, extensions_runner, process_errors
            )
        else:
            async with extensions_runner.executing():
                agen_or_result: Union[
                    OriginalExecutionResult,
                    AsyncGenerator[OriginalExecutionResult, None],
                ] = await original_subscribe(
                    schema,
                    execution_context.graphql_document,
                    root_value=execution_context.root_value,
                    variable_values=execution_context.variables,
                    operation_name=execution_context.operation_name,
                    context_value=execution_context.context,
                    middleware=middleware_manager,
                )

            # permission errors i.e would return here.
            if isinstance(agen_or_result, OriginalExecutionResult):
                yield await _handle_execution_result(
                    execution_context,
                    agen_or_result,
                    extensions_runner,
                    process_errors,
                )
            else:
                agen = agen_or_result.__aiter__()
                while True:
                    execution_context.extensions_results = {}
                    async with extensions_runner.executing():
                        try:
                            origin_result = await agen.__anext__()
                        except StopAsyncIteration:
                            break

                    yield await _handle_execution_result(
                        execution_context,
                        origin_result,
                        extensions_runner,
                        process_errors,
                    )
