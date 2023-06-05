from __future__ import annotations

from asyncio import ensure_future
from inspect import isawaitable
from typing import (
    TYPE_CHECKING,
    AsyncGenerator,
    AsyncIterable,
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

from graphql import ExecutionResult as GraphQLExecutionResult
from graphql import GraphQLError, parse
from graphql import execute as original_execute
from graphql import subscribe as original_subscribe
from graphql.validation import validate

from strawberry.exceptions import MissingQueryError
from strawberry.extensions.runner import SchemaExtensionsRunner
from strawberry.types import ExecutionResult

from .base import SubscribeSingleResult
from .exceptions import InvalidOperationTypeError

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Unpack

    from graphql import ExecutionContext as GraphQLExecutionContext
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


async def subscribe(
    schema: GraphQLSchema,
    *,
    extensions: Sequence[Union[Type[SchemaExtension], SchemaExtension]],
    execution_context: ExecutionContext,
    process_errors: Callable[[List[GraphQLError], Optional[ExecutionContext]], None],
) -> AsyncGenerator[ExecutionResult, None]:
    """
    The graphql-core subscribe function returns either an ExecutionResult or an
    AsyncGenerator[ExecutionResult, None].  The former is returned in case of an error
    during parsing or validation.
    Because we need to maintain execution context, we cannot return an
    async generator, we must _be_ an async generator.  So we yield a
    (bool, ExecutionResult) tuple, where the bool indicates whether the result is an
    potentially multiple execution result or a single result.
    A False value indicates an single result, most likely an intial
    failure (and no more values will be yielded) whereas a True value indicates a
    successful subscription, and more values may be yielded.
    """

    extensions_runner = SchemaExtensionsRunner(
        execution_context=execution_context,
        extensions=list(extensions),
    )

    # unlike execute(), the entire operation, including the results hooks,
    # is run within the operation() hook.
    async with extensions_runner.operation():
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead
        assert execution_context.query is not None

        async with extensions_runner.parsing():
            try:
                if not execution_context.graphql_document:
                    execution_context.graphql_document = parse_document(
                        execution_context.query, **execution_context.parse_options
                    )

            except GraphQLError as error:
                execution_context.errors = [error]
                process_errors([error], execution_context)
                raise SubscribeSingleResult(
                    ExecutionResult(
                        data=None,
                        errors=[error],
                        extensions=await extensions_runner.get_extensions_results(),
                    )
                )

            except Exception as error:  # pragma: no cover
                error = GraphQLError(str(error), original_error=error)
                execution_context.errors = [error]
                process_errors([error], execution_context)

                raise SubscribeSingleResult(
                    ExecutionResult(
                        data=None,
                        errors=[error],
                        extensions=await extensions_runner.get_extensions_results(),
                    )
                )

        async with extensions_runner.validation():
            _run_validation(execution_context)
            if execution_context.errors:
                process_errors(execution_context.errors, execution_context)
                raise SubscribeSingleResult(
                    ExecutionResult(data=None, errors=execution_context.errors)
                )

        async def process_result(result: GraphQLExecutionResult):
            execution_context.result = result
            # Also set errors on the execution_context so that it's easier
            # to access in extensions
            if result.errors:
                execution_context.errors = result.errors

                # Run the `Schema.process_errors` function here before
                # extensions have a chance to modify them (see the MaskErrors
                # extension). That way we can log the original errors but
                # only return a sanitised version to the client.
                process_errors(result.errors, execution_context)

            return ExecutionResult(
                data=execution_context.result.data,
                errors=execution_context.result.errors,
                extensions=await extensions_runner.get_extensions_results(),
            )

        async with extensions_runner.executing():
            # currently original_subscribe is an async function.  A future release
            # of graphql-core will make it optionally awaitable
            result: Union[AsyncIterable[GraphQLExecutionResult], GraphQLExecutionResult]
            result_or_awaitable = original_subscribe(
                schema,
                execution_context.graphql_document,
                root_value=execution_context.root_value,
                context_value=execution_context.context,
                variable_values=execution_context.variables,
                operation_name=execution_context.operation_name,
            )
            if isawaitable(result_or_awaitable):
                result = await cast(
                    Awaitable[
                        Union[
                            AsyncIterable["GraphQLExecutionResult"],
                            "GraphQLExecutionResult",
                        ]
                    ],
                    result_or_awaitable,
                )
            else:  # pragma: no cover
                result = cast(
                    Union[
                        AsyncIterable["GraphQLExecutionResult"],
                        "GraphQLExecutionResult",
                    ],
                    result_or_awaitable,
                )

            if isinstance(result, GraphQLExecutionResult):
                raise SubscribeSingleResult(await process_result(result))

            aiterator = result.__aiter__()
            try:
                async for result in aiterator:
                    yield await process_result(result)
            finally:
                # grapql-core's iterator may or may not have an aclose() method
                if hasattr(aiterator, "aclose"):
                    await aiterator.aclose()
