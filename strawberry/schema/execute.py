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
    Tuple,
    Type,
    TypedDict,
    Union,
    cast,
)

from graphql import ExecutionResult as GraphQLExecutionResult
from graphql import GraphQLError, parse
from graphql import execute as original_execute
from graphql.validation import validate

from strawberry.exceptions import MissingQueryError
from strawberry.schema.validation_rules.one_of import OneOfInputValidationRule
from strawberry.types import ExecutionResult
from strawberry.types.execution import PreExecutionError
from strawberry.utils.await_maybe import await_maybe

from .exceptions import InvalidOperationTypeError

if TYPE_CHECKING:
    from typing_extensions import NotRequired, TypeAlias, Unpack

    from graphql import ExecutionContext as GraphQLExecutionContext
    from graphql import GraphQLSchema
    from graphql.execution.middleware import MiddlewareManager
    from graphql.language import DocumentNode
    from graphql.validation import ASTValidationRule

    from strawberry.extensions.runner import SchemaExtensionsRunner
    from strawberry.types import ExecutionContext
    from strawberry.types.graphql import OperationType


# duplicated because of https://github.com/mkdocstrings/griffe-typingdoc/issues/7
class ParseOptions(TypedDict):
    max_tokens: NotRequired[int]


ProcessErrors: TypeAlias = (
    "Callable[[List[GraphQLError], Optional[ExecutionContext]], None]"
)


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


async def _parse_and_validate_async(
    context: ExecutionContext, extensions_runner: SchemaExtensionsRunner
) -> Optional[PreExecutionError]:
    if not context.query:
        raise MissingQueryError()

    async with extensions_runner.parsing():
        try:
            if not context.graphql_document:
                context.graphql_document = parse_document(context.query)

        except GraphQLError as error:
            context.errors = [error]
            return PreExecutionError(data=None, errors=[error])

        except Exception as error:
            error = GraphQLError(str(error), original_error=error)
            context.errors = [error]
            return PreExecutionError(data=None, errors=[error])

    if context.operation_type not in context.allowed_operations:
        raise InvalidOperationTypeError(context.operation_type)

    async with extensions_runner.validation():
        _run_validation(context)
        if context.errors:
            return PreExecutionError(
                data=None,
                errors=context.errors,
            )

    return None


async def _handle_execution_result(
    context: ExecutionContext,
    result: Union[GraphQLExecutionResult, ExecutionResult],
    extensions_runner: SchemaExtensionsRunner,
    process_errors: ProcessErrors | None,
) -> ExecutionResult:
    # Set errors on the context so that it's easier
    # to access in extensions
    if result.errors:
        context.errors = result.errors
        if process_errors:
            process_errors(result.errors, context)
    if isinstance(result, GraphQLExecutionResult):
        result = ExecutionResult(data=result.data, errors=result.errors)
    result.extensions = await extensions_runner.get_extensions_results(context)
    context.result = result  # type: ignore  # mypy failed to deduce correct type.
    return result


def _coerce_error(error: Union[GraphQLError, Exception]) -> GraphQLError:
    if isinstance(error, GraphQLError):
        return error
    return GraphQLError(str(error), original_error=error)


async def execute(
    schema: GraphQLSchema,
    execution_context: ExecutionContext,
    extensions_runner: SchemaExtensionsRunner,
    process_errors: ProcessErrors,
    middleware_manager: MiddlewareManager,
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
) -> ExecutionResult | PreExecutionError:
    try:
        async with extensions_runner.operation():
            # Note: In graphql-core the schema would be validated here but in
            # Strawberry we are validating it at initialisation time instead

            if errors := await _parse_and_validate_async(
                execution_context, extensions_runner
            ):
                return await _handle_execution_result(
                    execution_context, errors, extensions_runner, process_errors
                )

            assert execution_context.graphql_document
            async with extensions_runner.executing():
                if not execution_context.result:
                    result = await await_maybe(
                        original_execute(
                            schema,
                            execution_context.graphql_document,
                            root_value=execution_context.root_value,
                            middleware=middleware_manager,
                            variable_values=execution_context.variables,
                            operation_name=execution_context.operation_name,
                            context_value=execution_context.context,
                            execution_context_class=execution_context_class,
                        )
                    )
                    execution_context.result = result
                else:
                    result = execution_context.result
                # Also set errors on the execution_context so that it's easier
                # to access in extensions
                if result.errors:
                    execution_context.errors = result.errors

                    # Run the `Schema.process_errors` function here before
                    # extensions have a chance to modify them (see the MaskErrors
                    # extension). That way we can log the original errors but
                    # only return a sanitised version to the client.
                    process_errors(result.errors, execution_context)

    except (MissingQueryError, InvalidOperationTypeError) as e:
        raise e
    except Exception as exc:
        return await _handle_execution_result(
            execution_context,
            PreExecutionError(data=None, errors=[_coerce_error(exc)]),
            extensions_runner,
            process_errors,
        )
    # return results after all the operation completed.
    return await _handle_execution_result(
        execution_context, result, extensions_runner, None
    )


def execute_sync(
    schema: GraphQLSchema,
    *,
    allowed_operation_types: Iterable[OperationType],
    extensions_runner: SchemaExtensionsRunner,
    execution_context: ExecutionContext,
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
    process_errors: ProcessErrors,
    middleware_manager: MiddlewareManager,
) -> ExecutionResult:
    try:
        with extensions_runner.operation():
            # Note: In graphql-core the schema would be validated here but in
            # Strawberry we are validating it at initialisation time instead
            if not execution_context.query:
                raise MissingQueryError()

            with extensions_runner.parsing():
                try:
                    if not execution_context.graphql_document:
                        execution_context.graphql_document = parse_document(
                            execution_context.query, **execution_context.parse_options
                        )

                except GraphQLError as error:
                    execution_context.errors = [error]
                    process_errors([error], execution_context)
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
                    process_errors(execution_context.errors, execution_context)
                    return ExecutionResult(
                        data=None,
                        errors=execution_context.errors,
                        extensions=extensions_runner.get_extensions_results_sync(),
                    )

            with extensions_runner.executing():
                if not execution_context.result:
                    result = original_execute(
                        schema,
                        execution_context.graphql_document,
                        root_value=execution_context.root_value,
                        middleware=middleware_manager,
                        variable_values=execution_context.variables,
                        operation_name=execution_context.operation_name,
                        context_value=execution_context.context,
                        execution_context_class=execution_context_class,
                    )

                    if isawaitable(result):
                        result = cast(Awaitable[GraphQLExecutionResult], result)  # type: ignore[redundant-cast]
                        ensure_future(result).cancel()
                        raise RuntimeError(
                            "GraphQL execution failed to complete synchronously."
                        )

                    result = cast(GraphQLExecutionResult, result)  # type: ignore[redundant-cast]
                    execution_context.result = result
                    # Also set errors on the context so that it's easier
                    # to access in extensions
                    if result.errors:
                        execution_context.errors = result.errors

                        # Run the `Schema.process_errors` function here before
                        # extensions have a chance to modify them (see the MaskErrors
                        # extension). That way we can log the original errors but
                        # only return a sanitised version to the client.
                        process_errors(result.errors, execution_context)
    except (MissingQueryError, InvalidOperationTypeError) as e:
        raise e
    except Exception as exc:
        errors = [_coerce_error(exc)]
        execution_context.errors = errors
        process_errors(errors, execution_context)
        return ExecutionResult(
            data=None,
            errors=errors,
            extensions=extensions_runner.get_extensions_results_sync(),
        )
    return ExecutionResult(
        data=execution_context.result.data,
        errors=execution_context.result.errors,
        extensions=extensions_runner.get_extensions_results_sync(),
    )


__all__ = ["execute", "execute_sync"]
