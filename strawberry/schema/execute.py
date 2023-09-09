from __future__ import annotations

import contextlib
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

from graphql import GraphQLError, located_error, parse
from graphql import execute as original_execute
from graphql.validation import validate

from strawberry.exceptions import MissingQueryError
from strawberry.extensions.runner import SchemaExtensionsRunner
from strawberry.schema.validation_rules.one_of import OneOfInputValidationRule
from strawberry.types import ExecutionResult

from .exceptions import InvalidOperationTypeError

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Unpack

    from graphql import ExecutionContext as GraphQLExecutionContext
    from graphql import ExecutionResult as GraphQLExecutionResult
    from graphql import GraphQLSchema
    from graphql.language import DocumentNode
    from graphql.validation import ASTValidationRule

    from strawberry.extensions import SchemaExtension
    from strawberry.types import ExecutionContext
    from strawberry.types.graphql import OperationType


# duplicated because of https://github.com/mkdocstrings/griffe-typingdoc/issues/7
class ParseOptions(TypedDict):
    max_tokens: NotRequired[int]


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


def _initialize_partial_errors(execution_context: ExecutionContext) -> None:
    # Initialize a list of `Exceptions` on the context
    # Clients can add errors to this list but still return data, in
    # order to support partial results that contain both data and errors
    if execution_context.context is not None:
        try:
            execution_context.context.partial_errors: list[Exception] = []
        except AttributeError:
            with contextlib.suppress(TypeError, IndexError):
                execution_context.context["partial_errors"] = []


def _get_partial_errors(execution_context: ExecutionContext) -> list[GraphQLError]:
    # Pull any partial errors off the context
    partial_errors = []
    try:
        partial_errors = execution_context.context.partial_errors
    except AttributeError:
        with contextlib.suppress(TypeError, IndexError):
            partial_errors = execution_context.context["partial_errors"]

    # map each error to a `GraphQLError` if not one already
    return [
        error if isinstance(error, GraphQLError) else located_error(error)
        for error in partial_errors
    ]
    return []


async def execute(
    schema: GraphQLSchema,
    *,
    allowed_operation_types: Iterable[OperationType],
    extensions: Sequence[Union[Type[SchemaExtension], SchemaExtension]],
    execution_context: ExecutionContext,
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
    process_errors: Callable[[List[GraphQLError], Optional[ExecutionContext]], None],
) -> ExecutionResult:
    extensions_runner = SchemaExtensionsRunner(
        execution_context=execution_context,
        extensions=list(extensions),
    )

    try:
        async with extensions_runner.operation():
            # Note: In graphql-core the schema would be validated here but in
            # Strawberry we are validating it at initialisation time instead
            if not execution_context.query:
                raise MissingQueryError()

            async with extensions_runner.parsing():
                try:
                    if not execution_context.graphql_document:
                        execution_context.graphql_document = parse_document(
                            execution_context.query, **execution_context.parse_options
                        )

                except GraphQLError as exc:
                    execution_context.errors = [exc]
                    process_errors([exc], execution_context)
                    return ExecutionResult(
                        data=None,
                        errors=[exc],
                        extensions=await extensions_runner.get_extensions_results(),
                    )

            if execution_context.operation_type not in allowed_operation_types:
                raise InvalidOperationTypeError(execution_context.operation_type)

            async with extensions_runner.validation():
                _run_validation(execution_context)
                if execution_context.errors:
                    process_errors(execution_context.errors, execution_context)
                    return ExecutionResult(data=None, errors=execution_context.errors)

            async with extensions_runner.executing():
                if not execution_context.result:
                    _initialize_partial_errors(execution_context)

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
                        result = await cast(Awaitable["GraphQLExecutionResult"], result)

                    result = cast("GraphQLExecutionResult", result)
                    execution_context.result = result

                    partial_errors = _get_partial_errors(execution_context)
                    if partial_errors:
                        if not result.errors:
                            result.errors = []
                        # Add any partial errors manually added
                        # to the list of errors automatically added
                        result.errors.extend(partial_errors)

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
        error = (
            exc
            if isinstance(exc, GraphQLError)
            else GraphQLError(str(exc), original_error=exc)
        )
        execution_context.errors = [error]
        process_errors([error], execution_context)
        return ExecutionResult(
            data=None,
            errors=[error],
            extensions=await extensions_runner.get_extensions_results(),
        )

    return ExecutionResult(
        data=execution_context.result.data,
        errors=execution_context.result.errors,
        extensions=await extensions_runner.get_extensions_results(),
    )


def execute_sync(
    schema: GraphQLSchema,
    *,
    allowed_operation_types: Iterable[OperationType],
    extensions: Sequence[Union[Type[SchemaExtension], SchemaExtension]],
    execution_context: ExecutionContext,
    execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
    process_errors: Callable[[List[GraphQLError], Optional[ExecutionContext]], None],
) -> ExecutionResult:
    extensions_runner = SchemaExtensionsRunner(
        execution_context=execution_context,
        extensions=list(extensions),
    )

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

                except GraphQLError as exc:
                    execution_context.errors = [exc]
                    process_errors([exc], execution_context)
                    return ExecutionResult(
                        data=None,
                        errors=[exc],
                        extensions=extensions_runner.get_extensions_results_sync(),
                    )

            if execution_context.operation_type not in allowed_operation_types:
                raise InvalidOperationTypeError(execution_context.operation_type)

            with extensions_runner.validation():
                _run_validation(execution_context)
                if execution_context.errors:
                    process_errors(execution_context.errors, execution_context)
                    return ExecutionResult(data=None, errors=execution_context.errors)

            with extensions_runner.executing():
                if not execution_context.result:
                    _initialize_partial_errors(execution_context)

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
                        result = cast(Awaitable["GraphQLExecutionResult"], result)
                        ensure_future(result).cancel()
                        raise RuntimeError(
                            "GraphQL execution failed to complete synchronously."
                        )

                    result = cast("GraphQLExecutionResult", result)
                    execution_context.result = result

                    partial_errors = _get_partial_errors(execution_context)
                    if partial_errors:
                        if not result.errors:
                            result.errors = []
                        # Add any partial errors manually added
                        # to the list of errors automatically added
                        result.errors.extend(partial_errors)

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
        error = (
            exc
            if isinstance(exc, GraphQLError)
            else GraphQLError(str(exc), original_error=exc)
        )
        execution_context.errors = [error]
        process_errors([error], execution_context)
        return ExecutionResult(
            data=None,
            errors=[error],
            extensions=extensions_runner.get_extensions_results_sync(),
        )

    return ExecutionResult(
        data=execution_context.result.data,
        errors=execution_context.result.errors,
        extensions=extensions_runner.get_extensions_results_sync(),
    )
