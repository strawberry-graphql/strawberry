from asyncio import ensure_future
from inspect import isawaitable
from typing import (
    Awaitable,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)

from graphql import (
    ExecutionContext as GraphQLExecutionContext,
    ExecutionResult as GraphQLExecutionResult,
    GraphQLError,
    GraphQLSchema,
    execute as original_execute,
    parse,
)
from graphql.language import DocumentNode
from graphql.validation import ASTValidationRule, validate

from strawberry.extensions import Extension
from strawberry.extensions.runner import ExtensionsRunner
from strawberry.types import ExecutionContext, ExecutionResult
from strawberry.types.graphql import OperationType

from .exceptions import InvalidOperationTypeError


def parse_document(query: str) -> DocumentNode:
    return parse(query)


def validate_document(
    schema: GraphQLSchema,
    document: DocumentNode,
    validation_rules: Tuple[Type[ASTValidationRule], ...],
) -> List[GraphQLError]:
    return validate(
        schema,
        document,
        validation_rules,
    )


def _run_validation(execution_context: ExecutionContext) -> None:
    # Check if there are any validation rules or if validation has
    # already been run by an extension
    if len(execution_context.validation_rules) > 0 and execution_context.errors is None:
        assert execution_context.graphql_document
        execution_context.errors = validate_document(
            execution_context.schema._schema,
            execution_context.graphql_document,
            execution_context.validation_rules,
        )


async def execute(
    schema: GraphQLSchema,
    query: str,
    *,
    allowed_operation_types: Iterable[OperationType],
    extensions: Sequence[Union[Type[Extension], Extension]],
    execution_context: ExecutionContext,
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
) -> ExecutionResult:
    extensions_runner = ExtensionsRunner(
        execution_context=execution_context,
        extensions=list(extensions),
    )

    async with extensions_runner.request():
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead

        async with extensions_runner.parsing():
            try:
                if not execution_context.graphql_document:
                    execution_context.graphql_document = parse_document(query)

            except GraphQLError as error:
                execution_context.errors = [error]
                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=await extensions_runner.get_extensions_results(),
                )

            except Exception as error:  # pragma: no cover
                error = GraphQLError(str(error), original_error=error)

                execution_context.errors = [error]
                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=await extensions_runner.get_extensions_results(),
                )

        if execution_context.operation_type not in allowed_operation_types:
            raise InvalidOperationTypeError(execution_context.operation_type)

        async with extensions_runner.validation():
            _run_validation(execution_context)
            if execution_context.errors:
                return ExecutionResult(data=None, errors=execution_context.errors)

        async with extensions_runner.executing():
            if not execution_context.result:
                result = original_execute(
                    schema,
                    execution_context.graphql_document,
                    root_value=execution_context.root_value,
                    middleware=extensions_runner.as_middleware_manager(),
                    variable_values=execution_context.variables,
                    operation_name=execution_context.operation_name,
                    context_value=execution_context.context,
                    execution_context_class=execution_context_class,
                )

                if isawaitable(result):
                    result = await cast(Awaitable[GraphQLExecutionResult], result)

                result = cast(GraphQLExecutionResult, result)
                execution_context.result = result
                # Also set errors on the execution_context so that it's easier
                # to access in extensions
                if result.errors:
                    execution_context.errors = result.errors

    return ExecutionResult(
        data=execution_context.result.data,
        errors=execution_context.result.errors,
        extensions=await extensions_runner.get_extensions_results(),
    )


def execute_sync(
    schema: GraphQLSchema,
    query: str,
    *,
    allowed_operation_types: Iterable[OperationType],
    extensions: Sequence[Union[Type[Extension], Extension]],
    execution_context: ExecutionContext,
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
) -> ExecutionResult:
    extensions_runner = ExtensionsRunner(
        execution_context=execution_context,
        extensions=list(extensions),
    )

    with extensions_runner.request():
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead

        with extensions_runner.parsing():
            try:
                if not execution_context.graphql_document:
                    execution_context.graphql_document = parse_document(query)

            except GraphQLError as error:
                execution_context.errors = [error]
                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=extensions_runner.get_extensions_results_sync(),
                )

            except Exception as error:  # pragma: no cover
                error = GraphQLError(str(error), original_error=error)

                execution_context.errors = [error]
                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=extensions_runner.get_extensions_results_sync(),
                )

        if execution_context.operation_type not in allowed_operation_types:
            raise InvalidOperationTypeError(execution_context.operation_type)

        with extensions_runner.validation():
            _run_validation(execution_context)
            if execution_context.errors:
                return ExecutionResult(data=None, errors=execution_context.errors)

        with extensions_runner.executing():
            if not execution_context.result:
                result = original_execute(
                    schema,
                    execution_context.graphql_document,
                    root_value=execution_context.root_value,
                    middleware=extensions_runner.as_middleware_manager(),
                    variable_values=execution_context.variables,
                    operation_name=execution_context.operation_name,
                    context_value=execution_context.context,
                    execution_context_class=execution_context_class,
                )

                if isawaitable(result):
                    result = cast(Awaitable[GraphQLExecutionResult], result)
                    ensure_future(result).cancel()
                    raise RuntimeError(
                        "GraphQL execution failed to complete synchronously."
                    )

                result = cast(GraphQLExecutionResult, result)
                execution_context.result = result
                # Also set errors on the execution_context so that it's easier
                # to access in extensions
                if result.errors:
                    execution_context.errors = result.errors

    return ExecutionResult(
        data=execution_context.result.data,
        errors=execution_context.result.errors,
        extensions=extensions_runner.get_extensions_results_sync(),
    )
