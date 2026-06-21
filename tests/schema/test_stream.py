from collections.abc import AsyncGenerator

import pytest
from graphql import GraphQLError

import strawberry
from strawberry.extensions import MaxTokensLimiter, SchemaExtension
from strawberry.schema._graphql_core import GraphQLIncrementalExecutionResults
from strawberry.schema.config import StrawberryConfig
from strawberry.types.execution import ExecutionResult, PreExecutionError
from strawberry.types.graphql import OperationType
from strawberry.utils.aio import aclosing
from tests.conftest import skip_if_gql_32


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def echo(self, message: str) -> str:
        return message


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 3) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)


async def collect(stream):
    async with aclosing(stream) as results:
        return [result async for result in results]


@pytest.mark.asyncio
async def test_stream_query_yields_single_result():
    results = await collect(await schema.stream("{ hello }"))

    assert len(results) == 1
    assert not results[0].errors
    assert results[0].data == {"hello": "world"}


@pytest.mark.asyncio
async def test_stream_mutation_yields_single_result():
    results = await collect(await schema.stream('mutation { echo(message: "hi") }'))

    assert len(results) == 1
    assert results[0].data == {"echo": "hi"}


@pytest.mark.asyncio
async def test_stream_subscription_yields_multiple_results():
    results = await collect(await schema.stream("subscription { count(target: 3) }"))

    assert [result.data["count"] for result in results] == [0, 1, 2]


@pytest.mark.asyncio
async def test_stream_syntax_error_yields_single_pre_execution_error():
    results = await collect(await schema.stream("{ hello"))

    assert len(results) == 1
    assert isinstance(results[0], PreExecutionError)
    assert results[0].errors


@pytest.mark.asyncio
async def test_stream_validation_error_yields_single_pre_execution_error():
    results = await collect(await schema.stream("{ doesNotExist }"))

    assert len(results) == 1
    assert isinstance(results[0], PreExecutionError)
    assert results[0].errors


@pytest.mark.asyncio
async def test_stream_respects_parse_options_from_extensions():
    limited_schema = strawberry.Schema(
        query=Query,
        extensions=[lambda: MaxTokensLimiter(max_token_count=2)],
    )

    results = await collect(await limited_schema.stream("{ hello }"))

    assert len(results) == 1
    assert isinstance(results[0], PreExecutionError)
    assert results[0].errors
    assert (
        results[0].errors[0].message
        == "Syntax Error: Document contains more than 2 tokens. Parsing aborted."
    )


@pytest.mark.asyncio
async def test_stream_none_query_yields_single_pre_execution_error():
    results = await collect(await schema.stream(None))

    assert len(results) == 1
    assert isinstance(results[0], PreExecutionError)
    assert results[0].errors
    assert results[0].errors[0].message == 'Request data is missing a "query" value'


@pytest.mark.asyncio
async def test_stream_empty_query_yields_single_pre_execution_error():
    results = await collect(await schema.stream(""))

    assert len(results) == 1
    assert isinstance(results[0], PreExecutionError)
    assert results[0].errors
    assert results[0].errors[0].message == 'Request data is missing a "query" value'


@pytest.mark.asyncio
async def test_stream_query_processes_errors_exactly_once(mocker):
    @strawberry.type
    class ErrorQuery:
        @strawberry.field
        def boom(self) -> str:
            raise ValueError("boom")

    error_schema = strawberry.Schema(query=ErrorQuery)
    spy = mocker.spy(error_schema, "process_errors")

    results = await collect(await error_schema.stream("{ boom }"))

    assert len(results) == 1
    assert results[0].errors
    # The single-result path must run process_errors once (and not again via
    # _handle_execution_result), matching `Schema.execute`.
    spy.assert_called_once()


@pytest.mark.asyncio
async def test_stream_query_attaches_extension_results():
    class MyExtension(SchemaExtension):
        def get_results(self) -> dict[str, object]:
            return {"example": "result"}

    extended_schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    results = await collect(await extended_schema.stream("{ hello }"))

    assert len(results) == 1
    assert results[0].extensions == {"example": "result"}


@pytest.mark.asyncio
async def test_stream_disallowed_operation_type_yields_single_pre_execution_error():
    results = await collect(
        await schema.stream(
            "subscription { count }",
            allowed_operation_types=(OperationType.QUERY, OperationType.MUTATION),
        )
    )

    assert len(results) == 1
    assert isinstance(results[0], PreExecutionError)
    assert results[0].errors
    assert results[0].errors[0].message == "subscriptions are not allowed"


@skip_if_gql_32("GraphQL 3.3.0 is required for incremental execution")
@pytest.mark.asyncio
async def test_stream_expands_incremental_delivery():
    @strawberry.type
    class StreamQuery:
        @strawberry.field
        async def streamable_field(self) -> strawberry.Streamable[str]:
            for value in ["a", "b", "c"]:
                yield value

    incremental_schema = strawberry.Schema(
        query=StreamQuery,
        config=StrawberryConfig(enable_experimental_incremental_execution=True),
    )

    frames = await collect(
        await incremental_schema.stream("{ streamableField @stream }")
    )

    # The incremental container is expanded into discrete frames, not yielded
    # whole — so a streaming transport sees one uniform sequence of results.
    assert len(frames) >= 2
    assert not any(
        isinstance(frame, GraphQLIncrementalExecutionResults) for frame in frames
    )
    # First frame is the initial result; later frames carry the `@stream` patches.
    assert frames[0].data == {"streamableField": []}
    assert frames[0].has_next is True
    assert frames[-1].has_next is False
    assert any(getattr(frame, "incremental", None) for frame in frames[1:])


@pytest.mark.asyncio
async def test_stream_handles_incremental_initial_result(monkeypatch):
    from strawberry.schema import schema as schema_module

    processed_errors = []

    class MyExtension(SchemaExtension):
        def get_results(self) -> dict[str, object]:
            return {"example": "result"}

    class FakeSubsequentResults:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

        async def aclose(self) -> None:
            pass

    class FakeIncrementalExecutionResults:
        def __init__(self) -> None:
            self.initial_result = ExecutionResult(
                data=None,
                errors=[
                    GraphQLError(
                        "original error",
                        original_error=ValueError("original error"),
                    )
                ],
            )
            self.subsequent_results = FakeSubsequentResults()

    class CustomSchema(strawberry.Schema):
        def process_errors(self, errors, execution_context):
            processed_errors.append(errors[0])
            errors[0] = GraphQLError("masked error")

    incremental_result = FakeIncrementalExecutionResults()
    incremental_schema = CustomSchema(query=Query, extensions=[MyExtension])

    async def fake_execute_operation(*args: object, **kwargs: object):
        return incremental_result

    monkeypatch.setattr(
        schema_module,
        "GraphQLIncrementalExecutionResults",
        FakeIncrementalExecutionResults,
    )
    monkeypatch.setattr(
        incremental_schema,
        "_execute_operation",
        fake_execute_operation,
    )

    results = await collect(await incremental_schema.stream("{ hello }"))

    assert len(results) == 1
    assert results[0].errors
    assert results[0].errors[0].message == "masked error"
    assert results[0].extensions == {"example": "result"}
    assert processed_errors[0].message == "original error"


@pytest.mark.asyncio
async def test_stream_closes_incremental_subsequent_results_when_abandoned(monkeypatch):
    from strawberry.schema import schema as schema_module

    class FakeSubsequentResults:
        def __init__(self) -> None:
            self.closed = False
            self._remaining_results = ["patch"]

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self._remaining_results:
                return self._remaining_results.pop(0)

            raise StopAsyncIteration

        async def aclose(self) -> None:
            self.closed = True

    class FakeIncrementalExecutionResults:
        def __init__(self, subsequent_results: FakeSubsequentResults) -> None:
            self.initial_result = ExecutionResult(data={"initial": True}, errors=None)
            self.subsequent_results = subsequent_results

    subsequent_results = FakeSubsequentResults()
    incremental_result = FakeIncrementalExecutionResults(subsequent_results)
    incremental_schema = strawberry.Schema(query=Query)

    async def fake_execute_operation(*args: object, **kwargs: object):
        return incremental_result

    monkeypatch.setattr(
        schema_module,
        "GraphQLIncrementalExecutionResults",
        FakeIncrementalExecutionResults,
    )
    monkeypatch.setattr(
        incremental_schema,
        "_execute_operation",
        fake_execute_operation,
    )

    results = await incremental_schema.stream("{ hello }")

    initial_result = await results.__anext__()
    assert initial_result.data == {"initial": True}
    assert await results.__anext__() == "patch"
    assert not subsequent_results.closed

    await results.aclose()

    assert subsequent_results.closed
