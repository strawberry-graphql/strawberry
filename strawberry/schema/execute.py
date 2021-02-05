from asyncio import ensure_future
from inspect import isawaitable
from typing import Any, Awaitable, Dict, List, Optional, Sequence, Type, cast

from graphql import (
    ExecutionContext as GraphQLExecutionContext,
    ExecutionResult as GraphQLExecutionResult,
    GraphQLError,
    GraphQLSchema,
    execute as original_execute,
    parse,
)
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
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
    validate_queries: bool = True,
) -> ExecutionResult:
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
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead

        try:
            with extensions_runner.parsing():
                document = parse(query)
        except GraphQLError as error:
            return ExecutionResult(
                data=None,
                errors=[error],
                extensions=extensions_runner.get_extensions_results(),
            )

        except Exception as error:  # pragma: no cover
            error = GraphQLError(str(error), original_error=error)

            return ExecutionResult(
                data=None,
                errors=[error],
                extensions=extensions_runner.get_extensions_results(),
            )

        if validate_queries:
            with extensions_runner.validation():
                validation_errors = validate(schema, document)

            if validation_errors:
                return ExecutionResult(data=None, errors=validation_errors)

        result = original_execute(
            schema,
            document,
            root_value=root_value,
            middleware=extensions_runner.as_middleware_manager(*additional_middlewares),
            variable_values=variable_values,
            operation_name=operation_name,
            context_value=context_value,
            execution_context_class=execution_context_class,
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
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
    validate_queries: bool = True,
) -> ExecutionResult:
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
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead

        try:
            with extensions_runner.parsing():
                document = parse(query)
        except GraphQLError as error:
            return ExecutionResult(
                data=None,
                errors=[error],
                extensions=extensions_runner.get_extensions_results(),
            )

        except Exception as error:  # pragma: no cover
            error = GraphQLError(str(error), original_error=error)

            return ExecutionResult(
                data=None,
                errors=[error],
                extensions=extensions_runner.get_extensions_results(),
            )

        if validate_queries:
            with extensions_runner.validation():
                validation_errors = validate(schema, document)

            if validation_errors:
                return ExecutionResult(data=None, errors=validation_errors)

        result = original_execute(
            schema,
            document,
            root_value=root_value,
            middleware=extensions_runner.as_middleware_manager(*additional_middlewares),
            variable_values=variable_values,
            operation_name=operation_name,
            context_value=context_value,
            execution_context_class=execution_context_class,
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
