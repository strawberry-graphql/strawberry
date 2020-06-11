import typing
from inspect import isawaitable

from graphql import (
    ExecutionResult,
    GraphQLError,
    GraphQLSchema,
    execute as graphql_execute,
    parse,
)
from graphql.subscription import subscribe as graphql_subscribe
from graphql.type import validate_schema
from graphql.validation import validate

from .middleware import Middleware


async def execute(
    schema: GraphQLSchema,
    query: str,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    middleware: typing.List[Middleware] = None,
    operation_name: str = None,
):  # pragma: no cover
    schema_validation_errors = validate_schema(schema)
    if schema_validation_errors:
        return ExecutionResult(data=None, errors=schema_validation_errors)

    try:
        document = parse(query)
    except GraphQLError as error:
        return ExecutionResult(data=None, errors=[error])
    except Exception as error:
        error = GraphQLError(str(error), original_error=error)
        return ExecutionResult(data=None, errors=[error])

    validation_errors = validate(schema, document)

    if validation_errors:
        return ExecutionResult(data=None, errors=validation_errors)

    result = graphql_execute(
        schema,
        parse(query),
        root_value=root_value,
        middleware=middleware or [],
        variable_values=variable_values,
        operation_name=operation_name,
        context_value=context_value,
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
