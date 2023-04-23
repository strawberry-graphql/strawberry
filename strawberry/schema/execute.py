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

from .exceptions import InvalidOperationTypeError

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from graphql import ExecutionContext as GraphQLExecutionContext
    from graphql import GraphQLSchema
    from graphql.language import DocumentNode
    from graphql.validation import ASTValidationRule

    from strawberry.extensions import SchemaExtension
    from strawberry.types import ExecutionContext
    from strawberry.types.execution import ParseOptions
    from strawberry.types.graphql import OperationType


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


async def _parse_and_validate_async(
    execution_context: ExecutionContext,
    process_errors: Callable[[List[GraphQLError], Optional[ExecutionContext]], None],
    extensions_runner: SchemaExtensionsRunner,
    allowed_operation_types: Optional[Iterable[OperationType]] = None,
):
    assert execution_context.query
    async with extensions_runner.parsing():
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
                extensions=await extensions_runner.get_extensions_results(),
            )

        except Exception as error:  # pragma: no cover
            error = GraphQLError(str(error), original_error=error)

            execution_context.errors = [error]
            process_errors([error], execution_context)

            return ExecutionResult(
                data=None,
                errors=[error],
                extensions=await extensions_runner.get_extensions_results(),
            )

    if (
        allowed_operation_types is not None
        and execution_context.operation_type not in allowed_operation_types
    ):
        raise InvalidOperationTypeError(execution_context.operation_type)

    async with extensions_runner.validation():
        _run_validation(execution_context)
        if execution_context.errors:
            process_errors(execution_context.errors, execution_context)
            return ExecutionResult(data=None, errors=execution_context.errors)


def _parse_and_validate_sync(
    execution_context: ExecutionContext,
    process_errors: Callable[[List[GraphQLError], Optional[ExecutionContext]], None],
    extensions_runner: SchemaExtensionsRunner,
    allowed_operation_types: Iterable[OperationType],
) -> Optional[ExecutionResult]:
    assert execution_context.query
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

        except Exception as error:  # pragma: no cover
            error = GraphQLError(str(error), original_error=error)

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
            return ExecutionResult(data=None, errors=execution_context.errors)
    return None


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

    async with extensions_runner.operation():
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead
        if not execution_context.query:
            raise MissingQueryError()

        error_result = await _parse_and_validate_async(
            execution_context,
            process_errors,
            extensions_runner,
            allowed_operation_types,
        )
        if error_result is not None:
            return error_result

        async with extensions_runner.executing():
            if not execution_context.result:
                assert execution_context.graphql_document
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

    with extensions_runner.operation():
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead
        if not execution_context.query:
            raise MissingQueryError()

        error_result = _parse_and_validate_sync(
            execution_context,
            process_errors,
            extensions_runner,
            allowed_operation_types,
        )
        if error_result is not None:
            return error_result

        with extensions_runner.executing():
            if not execution_context.result:
                assert execution_context.graphql_document
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
) -> Union[ExecutionResult, AsyncGenerator[ExecutionResult, None]]:
    # The graphql-core subscribe function returns either an ExecutionResult or an
    # AsyncGenerator[ExecutionResult, None].  The former is returned in case of an error
    # during parsing or validation.
    # We repeat that pattern here, but to maintain the context of the extensions
    # context manager, we must delegate to an inner async generator.  The inner
    # generator yields an initial result, either a None, or an ExecutionResult,
    # to indicate the two different cases.

    asyncgen = _subscribe(
        schema,
        extensions=extensions,
        execution_context=execution_context,
        process_errors=process_errors,
    )
    # start the generator
    first = await asyncgen.__anext__()
    if first is not None:
        # Single result.  Close the generator to exit any context managers
        await asyncgen.aclose()
        return first
    else:
        # return the started generator. Cast away the Optional[] type
        return cast(AsyncGenerator[ExecutionResult, None], asyncgen)


async def _subscribe(
    schema: GraphQLSchema,
    *,
    extensions: Sequence[Union[Type[SchemaExtension], SchemaExtension]],
    execution_context: ExecutionContext,
    process_errors: Callable[[List[GraphQLError], Optional[ExecutionContext]], None],
) -> AsyncGenerator[Optional[ExecutionResult], None]:
    # This Async generator first yields either a single ExecutionResult or None.
    # If None is yielded, then the subscription has failed and the generator should
    # be closed.
    # Otherwise, if None is yielded, the subscription can continue.

    extensions_runner = SchemaExtensionsRunner(
        execution_context=execution_context,
        extensions=list(extensions),
    )

    # unlike execute(), the entire operation, including the results hooks,
    # is run within the operation() hook.
    async with extensions_runner.operation():
        # Note: In graphql-core the schema would be validated here but in
        # Strawberry we are validating it at initialisation time instead

        error_result = await _parse_and_validate_async(
            execution_context, process_errors, extensions_runner
        )
        if error_result is not None:
            yield error_result
            return  # pragma: no cover

        async with extensions_runner.executing():
            # currently original_subscribe is an async function.  A future release
            # of graphql-core will make it optionally awaitable
            assert execution_context.graphql_document
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
                yield await process_subscribe_result(
                    execution_context, process_errors, extensions_runner, result
                )
                return  # pragma: no cover

            yield None  # signal that we are returning an async generator
            aiterator = result.__aiter__()
            try:
                async for result in aiterator:
                    yield await process_subscribe_result(
                        execution_context, process_errors, extensions_runner, result
                    )
            finally:
                # grapql-core's iterator may or may not have an aclose() method
                if hasattr(aiterator, "aclose"):
                    await aiterator.aclose()


async def process_subscribe_result(
    execution_context: ExecutionContext,
    process_errors: Callable[[List[GraphQLError], Optional[ExecutionContext]], None],
    extensions_runner: SchemaExtensionsRunner,
    result: GraphQLExecutionResult,
) -> ExecutionResult:
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
