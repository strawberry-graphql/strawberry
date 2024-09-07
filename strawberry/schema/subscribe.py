from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, AsyncIterator, Optional, Type, Union

from graphql import (
    ExecutionResult as OriginalExecutionResult,
)
from graphql.execution import ExecutionContext as GraphQLExecutionContext
from graphql.execution import subscribe as original_subscribe

from strawberry.types import ExecutionResult
from strawberry.types.execution import ExecutionContext, PreExecutionError
from strawberry.utils import IS_GQL_32
from strawberry.utils.await_maybe import await_maybe

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
    PreExecutionError, AsyncGenerator[ExecutionResult, None]
]

OriginSubscriptionResult = Union[
    OriginalExecutionResult,
    AsyncIterator[OriginalExecutionResult],
]


async def _subscribe(
    schema: GraphQLSchema,
    execution_context: ExecutionContext,
    extensions_runner: SchemaExtensionsRunner,
    process_errors: ProcessErrors,
    middleware_manager: MiddlewareManager,
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
) -> AsyncGenerator[Union[PreExecutionError, ExecutionResult], None]:
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
        try:
            async with extensions_runner.executing():
                assert execution_context.graphql_document is not None
                gql_33_kwargs = {
                    "middleware": middleware_manager,
                    "execution_context_class": execution_context_class,
                }
                try:
                    # Might not be awaitable for pre-execution errors.
                    aiter_or_result: OriginSubscriptionResult = await await_maybe(
                        original_subscribe(
                            schema,
                            execution_context.graphql_document,
                            root_value=execution_context.root_value,
                            variable_values=execution_context.variables,
                            operation_name=execution_context.operation_name,
                            context_value=execution_context.context,
                            **{} if IS_GQL_32 else gql_33_kwargs,  # type: ignore[arg-type]
                        )
                    )
                # graphql-core 3.2 doesn't handle some of the pre-execution errors.
                # see `test_subscription_immediate_error`
                except Exception as exc:
                    aiter_or_result = OriginalExecutionResult(
                        data=None, errors=[_coerce_error(exc)]
                    )

            # Handle pre-execution errors.
            if isinstance(aiter_or_result, OriginalExecutionResult):
                yield await _handle_execution_result(
                    execution_context,
                    PreExecutionError(data=None, errors=aiter_or_result.errors),
                    extensions_runner,
                    process_errors,
                )
            else:
                try:
                    async for result in aiter_or_result:
                        yield await _handle_execution_result(
                            execution_context,
                            result,
                            extensions_runner,
                            process_errors,
                        )
                # graphql-core doesn't handle exceptions raised while executing.
                except Exception as exc:
                    yield await _handle_execution_result(
                        execution_context,
                        OriginalExecutionResult(data=None, errors=[_coerce_error(exc)]),
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
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
) -> SubscriptionResult:
    asyncgen = _subscribe(
        schema,
        execution_context,
        extensions_runner,
        process_errors,
        middleware_manager,
        execution_context_class,
    )
    # GrapQL-core might return an initial error result instead of an async iterator.
    # This happens when "there was an immediate error" i.e resolver is not an async iterator.
    # To overcome this while maintaining the extension contexts we do this trick.
    first = await asyncgen.__anext__()
    if isinstance(first, PreExecutionError):
        await asyncgen.aclose()
        return first

    async def _wrapper() -> AsyncGenerator[ExecutionResult, None]:
        yield first
        async for result in asyncgen:
            yield result

    return _wrapper()
