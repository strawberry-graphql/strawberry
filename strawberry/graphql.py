import typing

from graphql import ExecutionResult, GraphQLSchema, parse
from graphql.subscription import subscribe as graphql_subscribe


async def subscribe(
    schema: GraphQLSchema,
    query: str,
    root_value: typing.Any = None,
    context_value: typing.Any = None,
    variable_values: typing.Dict[str, typing.Any] = None,
    operation_name: str = None,
) -> typing.Union[typing.AsyncIterator[ExecutionResult], ExecutionResult]:
    document = parse(query)

    return await graphql_subscribe(
        schema=schema,
        document=document,
        root_value=root_value,
        context_value=context_value,
        variable_values=variable_values,
        operation_name=operation_name,
    )
