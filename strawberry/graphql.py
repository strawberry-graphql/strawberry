import dataclasses
import typing
from asyncio import ensure_future
from inspect import isawaitable

from graphql import (
    ExecutionResult as GraphQLExecutionResult,
    GraphQLError,
    GraphQLSchema,
    execute as graphql_excute,
    parse,
)
from graphql.pyutils import AwaitableOrValue
from graphql.subscription import subscribe as graphql_subscribe
from graphql.type import validate_schema
from graphql.validation import validate

from .extensions import ExtensionsRunner
from .middleware import DirectivesMiddleware
from .schema import Schema


@dataclasses.dataclass
class ExecutionResult:
    data: typing.Optional[typing.Dict[str, typing.Any]]
    errors: typing.Optional[typing.List[GraphQLError]]
    extensions: typing.Optional[typing.Dict[str, typing.Any]] = None


def _execute(
    schema: Schema,
    query: str,
    extensions_runner: ExtensionsRunner,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    operation_name: str = None,
) -> AwaitableOrValue[GraphQLExecutionResult]:
    with extensions_runner.request():
        schema_validation_errors = validate_schema(schema)

        if schema_validation_errors:
            return GraphQLExecutionResult(data=None, errors=schema_validation_errors)

        try:
            with extensions_runner.parsing():
                document = parse(query)
        except GraphQLError as error:
            return GraphQLExecutionResult(data=None, errors=[error])

        except Exception as error:
            error = GraphQLError(str(error), original_error=error)

            return GraphQLExecutionResult(data=None, errors=[error])

        with extensions_runner.validation():
            validation_errors = validate(schema, document)

        if validation_errors:
            return GraphQLExecutionResult(data=None, errors=validation_errors)

        return graphql_excute(
            schema,
            document,
            root_value=root_value,
            middleware=extensions_runner.as_middleware_manager(DirectivesMiddleware()),
            variable_values=variable_values,
            operation_name=operation_name,
            context_value=context_value,
        )


def execute_sync(
    schema: Schema,
    query: str,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    operation_name: str = None,
) -> ExecutionResult:
    extensions_runner = ExtensionsRunner(schema.strawberry_extensions)

    result = _execute(
        schema=schema,
        query=query,
        extensions_runner=extensions_runner,
        root_value=root_value,
        context_value=context_value,
        variable_values=variable_values,
        operation_name=operation_name,
    )

    # Assert that the execution was synchronous.
    if isawaitable(result):
        ensure_future(typing.cast(typing.Awaitable[ExecutionResult], result)).cancel()

        raise RuntimeError("GraphQL execution failed to complete synchronously.")

    result = typing.cast(GraphQLExecutionResult, result)

    return ExecutionResult(
        data=result.data,
        errors=result.errors,
        extensions=extensions_runner.get_extensions_results(),
    )


async def execute(
    schema: Schema,
    query: str,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    operation_name: str = None,
):
    extensions_runner = ExtensionsRunner(schema.strawberry_extensions)

    result = _execute(
        schema=schema,
        query=query,
        extensions_runner=extensions_runner,
        root_value=root_value,
        context_value=context_value,
        variable_values=variable_values,
        operation_name=operation_name,
    )

    if isawaitable(result):
        result = await typing.cast(typing.Awaitable[GraphQLExecutionResult], result)

    result = typing.cast(GraphQLExecutionResult, result)

    return ExecutionResult(
        data=result.data,
        errors=result.errors,
        extensions=extensions_runner.get_extensions_results(),
    )


async def subscribe(
    schema: GraphQLSchema,
    query: str,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    operation_name: str = None,
) -> typing.Union[typing.AsyncIterator[GraphQLExecutionResult], GraphQLExecutionResult]:
    document = parse(query)

    return await graphql_subscribe(
        schema=schema,
        document=document,
        root_value=root_value,
        context_value=context_value,
        variable_values=variable_values,
        operation_name=operation_name,
    )
