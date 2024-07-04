from __future__ import annotations

from typing import AsyncGenerator, Union
from typing_extensions import TypeAlias

from graphql import (
    ExecutionResult as OriginalExecutionResult,
)
from graphql.execution import subscribe as original_subscribe
from graphql.execution.middleware import MiddlewareManager
from graphql.type.schema import GraphQLSchema

from strawberry.types import ExecutionResult
from strawberry.types.execution import ExecutionContext, ExecutionResultError

from ..extensions.runner import SchemaExtensionsRunner
from .execute import ProccessErrors, _handle_execution_result, _parse_and_validate_async

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
                    try:
                        while True:
                            async with extensions_runner.executing():
                                origin_result = await agen.__anext__()
                                yield await _handle_execution_result(
                                    execution_context,
                                    origin_result,
                                    extensions_runner,
                                    process_errors,
                                )
                    except StopAsyncIteration:
                        ...
