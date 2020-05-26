import dataclasses
import typing
from asyncio import ensure_future
from inspect import isawaitable

from graphql import GraphQLError, GraphQLSchema, execute as graphql_excute, parse
from graphql.subscription import subscribe as graphql_subscribe
from graphql.type import validate_schema
from graphql.validation import validate

from .middleware import DirectivesMiddleware, Middleware, SyncTracingMiddleware


@dataclasses.dataclass
class ExecutionResult:
    data: typing.Optional[typing.Dict[str, typing.Any]]
    errors: typing.Optional[typing.List[GraphQLError]]
    extensions: typing.Optional[typing.Dict[str, typing.Any]] = None


def _execute(
    # TODO: GraphQLSchema should really be a Strawberry GraphQL schema
    schema: GraphQLSchema,
    query: str,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    middleware: typing.List[Middleware] = None,
    operation_name: str = None,
    enable_tracing: bool = False,
):
    enabled_middlewares: typing.List[typing.Any] = [DirectivesMiddleware()]

    if enable_tracing:
        tracing_middleware = SyncTracingMiddleware()
        enabled_middlewares.append(tracing_middleware)
        tracing_middleware.start()

    schema_validation_errors = validate_schema(schema)

    if schema_validation_errors:
        return ExecutionResult(data=None, errors=schema_validation_errors)

    try:
        if enable_tracing:
            tracing_middleware.start_parsing()

        document = parse(query)

        if enable_tracing:
            tracing_middleware.end_parsing()

    except GraphQLError as error:
        return ExecutionResult(data=None, errors=[error])
    except Exception as error:
        error = GraphQLError(str(error), original_error=error)
        return ExecutionResult(data=None, errors=[error])

    if enable_tracing:
        tracing_middleware.start_validation()

    validation_errors = validate(schema, document)

    if validation_errors:
        return ExecutionResult(data=None, errors=validation_errors)

    if enable_tracing:
        tracing_middleware.end_validation()

    extensions = {}

    result = graphql_excute(
        schema,
        parse(query),
        root_value=root_value,
        middleware=enabled_middlewares,
        variable_values=variable_values,
        operation_name=operation_name,
        context_value=context_value,
    )

    if enable_tracing:
        tracing_middleware.stop()
        extensions["tracing"] = tracing_middleware.stats.to_json()

    return ExecutionResult(
        data=result.data, errors=result.errors, extensions=extensions
    )


def execute_sync(
    schema: GraphQLSchema,
    query: str,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    operation_name: str = None,
    middleware: typing.List[typing.Any] = None,
    enable_tracing: bool = False,
):
    result = _execute(
        schema=schema,
        query=query,
        root_value=root_value,
        context_value=context_value,
        variable_values=variable_values,
        operation_name=operation_name,
        middleware=middleware,
        enable_tracing=enable_tracing,
    )

    # Assert that the execution was synchronous.
    if isawaitable(result):
        ensure_future(typing.cast(typing.Awaitable[ExecutionResult], result)).cancel()

        raise RuntimeError("GraphQL execution failed to complete synchronously.")

    return typing.cast(ExecutionResult, result)


async def execute(
    schema: GraphQLSchema,
    query: str,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    operation_name: str = None,
    middleware: typing.List[typing.Any] = None,
    enable_tracing: bool = False,
):
    result = _execute(
        schema=schema,
        query=query,
        root_value=root_value,
        context_value=context_value,
        variable_values=variable_values,
        operation_name=operation_name,
        middleware=middleware,
        enable_tracing=enable_tracing,
    )

    if isawaitable(result):
        result = await typing.cast(typing.Awaitable[ExecutionResult], result)

    return result


async def subscribe(
    schema: GraphQLSchema,
    query: str,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    operation_name: str = None,
) -> typing.Union[
    typing.AsyncIterator[ExecutionResult], ExecutionResult
]:  # pragma: no cover
    document = parse(query)

    return await graphql_subscribe(
        schema=schema,
        document=document,
        root_value=root_value,
        context_value=context_value,
        variable_values=variable_values,
        operation_name=operation_name,
    )
