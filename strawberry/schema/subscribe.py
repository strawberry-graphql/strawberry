from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, AsyncGenerator, AsyncIterator, Union

from graphql import (
    ExecutionResult as OriginalExecutionResult,
)
from graphql.execution import subscribe as original_subscribe

from strawberry.types import ExecutionResult
from strawberry.types.execution import ExecutionContext, ExecutionResultError

from .execute import (
    ProcessErrors,
    _coerce_error,
    _handle_execution_result,
    _parse_and_validate_async,
)

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from graphql.execution.middleware import MiddlewareManager
    from graphql.type.schema import GraphQLSchema

    from ..extensions.runner import SchemaExtensionsRunner

SubscriptionResult: TypeAlias = Union[
    ExecutionResultError, AsyncIterator[ExecutionResult]
]


async def _subscribe(
    schema: GraphQLSchema,
    execution_context: ExecutionContext,
    extensions_runner: SchemaExtensionsRunner,
    process_errors: ProcessErrors,
    middleware_manager: MiddlewareManager,
) -> AsyncGenerator[Union[ExecutionResultError, ExecutionResult], None]:
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

        if isinstance(agen_or_result, OriginalExecutionResult):
            yield await _handle_execution_result(
                execution_context,
                ExecutionResultError(data=None, errors=agen_or_result.errors),
                extensions_runner,
                process_errors,
            )
            execution_context.extensions_results = {}

        else:
            aiterator = agen_or_result.__aiter__()
            running = True
            while running:
                # reset extensions results for each iteration
                execution_context.extensions_results = {}
                try:
                    async with extensions_runner.executing():
                        try:
                            origin_result = await aiterator.__anext__()

                        except StopAsyncIteration:
                            break
                        except Exception as exc:
                            # graphql-core doesn't handle exceptions raised in the async generator.
                            origin_result = ExecutionResult(
                                data=None, errors=[_coerce_error(exc)]
                            )
                            running = False
                    # we could have yielded in the except block above.
                    # but this way we make sure `get_result` hook is called deterministically after
                    # `on_execute` hook is done.
                    yield await _handle_execution_result(
                        execution_context,
                        origin_result,
                        extensions_runner,
                        process_errors,
                    )
                # catch exceptions raised in `on_execute` hook.
                except Exception as exc:
                    origin_result = OriginalExecutionResult(
                        data=None, errors=[_coerce_error(exc)]
                    )
                    yield await _handle_execution_result(
                        execution_context,
                        origin_result,
                        extensions_runner,
                        process_errors,
                    )


async def subscribe(
    schema: GraphQLSchema,
    execution_context: ExecutionContext,
    extensions_runner: SchemaExtensionsRunner,
    process_errors: ProcessErrors,
    middleware_manager: MiddlewareManager,
) -> SubscriptionResult:
    asyncgen = _subscribe(
        schema,
        execution_context,
        extensions_runner,
        process_errors,
        middleware_manager,
    )
    # GrapQL-core might return an initial error result instead of an async iterator.
    # This happens when "there was an immediate error" i.e resolver is not an async iterator.
    # To overcome this while maintaining the extension contexts we do this trick.
    first = await asyncgen.__anext__()
    if isinstance(first, ExecutionResultError):
        # close the async generator (calling `.aclose()` on it won't close the context managers)
        with contextlib.suppress(StopAsyncIteration):
            await asyncgen.__anext__()
        return first
    else:

        async def _wrapper() -> AsyncIterator[ExecutionResult]:
            yield first
            async for result in asyncgen:
                yield result

        return _wrapper()
