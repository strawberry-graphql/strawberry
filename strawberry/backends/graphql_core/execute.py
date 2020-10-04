from asyncio import ensure_future
from inspect import isawaitable
from typing import Any, Awaitable, Dict, List, Sequence, Tuple, Type, cast

from graphql import (
    ExecutionResult as GraphQLExecutionResult,
    GraphQLError,
    GraphQLSchema,
    execute as original_execute,
    parse,
)
from graphql.pyutils import AwaitableOrValue
from graphql.type import validate_schema
from graphql.validation import validate
from strawberry.extensions import Extension
from strawberry.extensions.runner import ExtensionsRunner
from strawberry.types import ExecutionContext, ExecutionResult


async def execute(
    schema: GraphQLSchema,
    query: str,
    extensions: Sequence[Type[Extension]],
    root_value: Any = None,
    context_value: Any = None,
    variable_values: Dict[str, Any] = None,
    additional_middlewares: List[Any] = None,
    operation_name: str = None,
) -> ExecutionResult:
    result, extensions_runner = base_execute(
        schema=schema,
        query=query,
        extensions=extensions,
        root_value=root_value,
        context_value=context_value,
        variable_values=variable_values,
        additional_middlewares=additional_middlewares,
        operation_name=operation_name,
    )

    if isawaitable(result):
        result = await cast(Awaitable[GraphQLExecutionResult], result)

    result = cast(GraphQLExecutionResult, result)

    return ExecutionResult(
        data=result.data,
        errors=result.errors,
        extensions=extensions_runner.get_extensions_results(),
    )


def execute_sync(
    schema: GraphQLSchema,
    query: str,
    extensions: Sequence[Type[Extension]],
    root_value: Any = None,
    context_value: Any = None,
    variable_values: Dict[str, Any] = None,
    additional_middlewares: List[Any] = None,
    operation_name: str = None,
) -> ExecutionResult:
    result, extensions_runner = base_execute(
        schema=schema,
        query=query,
        extensions=extensions,
        root_value=root_value,
        context_value=context_value,
        variable_values=variable_values,
        additional_middlewares=additional_middlewares,
        operation_name=operation_name,
    )

    if isawaitable(result):
        ensure_future(cast(Awaitable[GraphQLExecutionResult], result)).cancel()
        raise RuntimeError("GraphQL execution failed to complete synchronously.")

    result = cast(GraphQLExecutionResult, result)

    return ExecutionResult(
        data=result.data,
        errors=result.errors,
        extensions=extensions_runner.get_extensions_results(),
    )


def base_execute(
    schema: GraphQLSchema,
    query: str,
    extensions: Sequence[Type[Extension]],
    root_value: Any = None,
    context_value: Any = None,
    variable_values: Dict[str, Any] = None,
    additional_middlewares: List[Any] = None,
    operation_name: str = None,
) -> Tuple[AwaitableOrValue[GraphQLExecutionResult], ExtensionsRunner]:
    execution_context = ExecutionContext(
        query=query,
        context=context_value,
        variables=variable_values,
        operation_name=operation_name,
    )
    extensions_runner = ExtensionsRunner(
        execution_context=execution_context,
        extensions=[extension() for extension in extensions],
    )

    additional_middlewares = additional_middlewares or []

    with extensions_runner.request():
        schema_validation_errors = validate_schema(schema)

        if schema_validation_errors:
            return (
                GraphQLExecutionResult(data=None, errors=schema_validation_errors),
                extensions_runner,
            )

        try:
            with extensions_runner.parsing():
                document = parse(query)
        except GraphQLError as error:
            return GraphQLExecutionResult(data=None, errors=[error]), extensions_runner

        except Exception as error:  # pragma: no cover
            error = GraphQLError(str(error), original_error=error)

            return GraphQLExecutionResult(data=None, errors=[error]), extensions_runner

        with extensions_runner.validation():
            validation_errors = validate(schema, document)

        if validation_errors:
            return (
                GraphQLExecutionResult(data=None, errors=validation_errors),
                extensions_runner,
            )

        result = original_execute(
            schema,
            document,
            root_value=root_value,
            middleware=extensions_runner.as_middleware_manager(*additional_middlewares),
            variable_values=variable_values,
            operation_name=operation_name,
            context_value=context_value,
        )

    return result, extensions_runner
