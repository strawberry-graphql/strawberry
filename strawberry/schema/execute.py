from __future__ import annotations

from asyncio import ensure_future
from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    Awaitable,
    Callable,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypedDict,
    Union,
    cast,
)
from typing_extensions import NotRequired, Unpack

from graphql import ExecutionResult as GraphQLExecutionResult
from graphql import GraphQLError, parse
from graphql import execute as original_execute
from graphql.validation import validate

from strawberry.exceptions import MissingQueryError
from strawberry.extensions.runner import SchemaExtensionsRunner
from strawberry.schema.validation_rules.one_of import OneOfInputValidationRule
from strawberry.types import ExecutionResult
from strawberry.types.execution import ExecutionResultError

from .exceptions import InvalidOperationTypeError

if TYPE_CHECKING:
    from graphql import ExecutionContext as GraphQLExecutionContext
    from graphql import GraphQLSchema
    from graphql.execution.middleware import MiddlewareManager
    from graphql.language import DocumentNode
    from graphql.validation import ASTValidationRule

    from strawberry.extensions import SchemaExtension
    from strawberry.types import ExecutionContext
    from strawberry.types.graphql import OperationType


# duplicated because of https://github.com/mkdocstrings/griffe-typingdoc/issues/7
class ParseOptions(TypedDict):
    max_tokens: NotRequired[int]


ProccessErrors = Callable[[List[GraphQLError], Optional[ExecutionContext]], None]


def parse_document(query: str, **kwargs: Unpack[ParseOptions]) -> DocumentNode:
    return parse(query, **kwargs)


def validate_document(
    schema: GraphQLSchema,
    document: DocumentNode,
    validation_rules: Tuple[Type[ASTValidationRule], ...],
) -> List[GraphQLError]:
    validation_rules = (
        *validation_rules,
        OneOfInputValidationRule,
    )
    return validate(
        schema,
        document,
        validation_rules,
    )


def _run_validation(context: ExecutionContext) -> None:
    # Check if there are any validation rules or if validation has
    # already been run by an extension
    if len(context.validation_rules) > 0 and context.errors is None:
        assert context.graphql_document
        context.errors = validate_document(
            context.schema._schema,
            context.graphql_document,
            context.validation_rules,
        )


def execute_sync(
    schema: GraphQLSchema,
    middleware_manager: MiddlewareManager,
    *,
    allowed_operation_types: Iterable[OperationType],
    extensions: Sequence[SchemaExtension],
    context: ExecutionContext,
    context_class: Optional[Type[GraphQLExecutionContext]] = None,
    process_errors: ProccessErrors,
) -> ExecutionResult:
    extensions_runner = SchemaExtensionsRunner(
        execution_context=context,
        extensions=list(extensions),
    )

    with extensions_runner.operation():
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead
        if not context.query:
            raise MissingQueryError()

        with extensions_runner.parsing():
            try:
                if not context.graphql_document:
                    context.graphql_document = parse_document(
                        context.query, **context.parse_options
                    )

            except GraphQLError as error:
                context.errors = [error]
                process_errors([error], context)
                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=extensions_runner.get_extensions_results_sync(),
                )

            except Exception as error:  # pragma: no cover
                error = GraphQLError(str(error), original_error=error)

                context.errors = [error]
                process_errors([error], context)

                return ExecutionResult(
                    data=None,
                    errors=[error],
                    extensions=extensions_runner.get_extensions_results_sync(),
                )

        if context.operation_type not in allowed_operation_types:
            raise InvalidOperationTypeError(context.operation_type)

        with extensions_runner.validation():
            _run_validation(context)
            if context.errors:
                process_errors(context.errors, context)
                return ExecutionResult(data=None, errors=context.errors)

        with extensions_runner.executing():
            if not context.result:
                result = original_execute(
                    schema,
                    context.graphql_document,
                    root_value=context.root_value,
                    middleware=middleware_manager,
                    variable_values=context.variables,
                    operation_name=context.operation_name,
                    context_value=context.context,
                    context_class=context_class,
                )

                if isawaitable(result):
                    result = cast(Awaitable[GraphQLExecutionResult], result)
                    ensure_future(result).cancel()
                    raise RuntimeError(
                        "GraphQL execution failed to complete synchronously."
                    )

                result = cast("GraphQLExecutionResult", result)
                context.result = result
                # Also set errors on the context so that it's easier
                # to access in extensions
                if result.errors:
                    context.errors = result.errors

                    # Run the `Schema.process_errors` function here before
                    # extensions have a chance to modify them (see the MaskErrors
                    # extension). That way we can log the original errors but
                    # only return a sanitised version to the client.
                    process_errors(result.errors, context)

    return ExecutionResult(
        data=context.result.data,
        errors=context.result.errors,
        extensions=extensions_runner.get_extensions_results_sync(),
    )


async def _parse_and_validate_async(
    context: ExecutionContext, extensions_runner: SchemaExtensionsRunner
) -> Optional[ExecutionResultError]:
    async with extensions_runner.parsing():
        if not context.query:
            raise MissingQueryError()
        try:
            if not context.graphql_document:
                context.graphql_document = parse_document(context.query)

        except GraphQLError as error:
            context.errors = [error]
            return ExecutionResultError(data=None, errors=[error])

        except Exception as error:
            error = GraphQLError(str(error), original_error=error)
            context.errors = [error]
            return ExecutionResultError(data=None, errors=[error])

    if context.operation_type not in context.allowed_operations:
        raise InvalidOperationTypeError(context.operation_type)

    async with extensions_runner.validation():
        _run_validation(context)
        if context.errors:
            return ExecutionResultError(
                data=None,
                errors=context.errors,
            )

    return None


async def _handle_execution_result(
    context: ExecutionContext,
    result: Union[GraphQLExecutionResult, ExecutionResult],
    extensions_runner: SchemaExtensionsRunner,
    process_errors: ProccessErrors,
) -> ExecutionResult:
    # Set errors on the context so that it's easier
    # to access in extensions
    if result.errors:
        context.errors = result.errors

        # Run the `Schema.process_errors` function here before
        # extensions have a chance to modify them (see the MaskErrors
        # extension). That way we can log the original errors but
        # only return a sanitised version to the client.
        process_errors(result.errors, context)
    if isinstance(result, GraphQLExecutionResult):
        result = ExecutionResult(data=result.data, errors=result.errors)
    result.extensions = await extensions_runner.get_extensions_results(context)
    context.result = result  # type: ignore  # mypy failed to deduce correct type.
    return result


async def execute(
    context: ExecutionContext,
    extensions_runner: SchemaExtensionsRunner,
    process_errors: ProccessErrors,
) -> Union[ExecutionResult, ExecutionResultError]:
    async with extensions_runner.operation():
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead

        errors = await _parse_and_validate_async(context, extensions_runner)
        if errors:
            return cast(
                ExecutionResultError,
                await _handle_execution_result(
                    context, errors, extensions_runner, process_errors
                ),
            )
        assert context.graphql_document
        # if there was no parsing error
        async with extensions_runner.executing():
            if not context.result:
                awaitable_or_res = original_execute(
                    context.schema,
                    context.graphql_document,
                    root_value=context.root_value,
                    middleware=context.middleware_manager,
                    variable_values=context.variables,
                    operation_name=context.operation_name,
                    context_value=context.context,
                    context_class=context.context_class,
                )

                if isawaitable(awaitable_or_res):
                    res = await awaitable_or_res
                else:
                    res = awaitable_or_res
            else:
                res = context.result
    # return results after all the operation completed.
    return await _handle_execution_result(
        context, res, extensions_runner, process_errors
    )
