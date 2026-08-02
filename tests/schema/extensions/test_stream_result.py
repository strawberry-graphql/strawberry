import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Iterator

import pytest

import strawberry
from strawberry.extensions import MaskErrors, SchemaExtension
from strawberry.schema._graphql_core import (
    InitialIncrementalExecutionResult,
    SubsequentIncrementalExecutionResult,
)
from strawberry.schema.config import StrawberryConfig
from strawberry.types import ExecutionResult, StreamExecutionResult
from tests.conftest import skip_if_gql_32


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"

    @strawberry.field
    def dangerous_query(self) -> str:
        raise RuntimeError("Secret query error")


@strawberry.type
class Mutation:
    @strawberry.mutation
    def dangerous_mutation(self) -> str:
        raise RuntimeError("Secret mutation error")


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self) -> AsyncGenerator[int, None]:
        yield 1
        yield 2

    @strawberry.subscription
    async def dangerous_stream(self) -> AsyncGenerator[int, None]:
        yield 1
        raise RuntimeError("Secret subscription error")


@strawberry.type
class DeferredPayload:
    @strawberry.field
    def dangerous(self) -> str | None:
        raise RuntimeError("Secret deferred error")


@strawberry.type
class IncrementalQuery:
    @strawberry.field
    async def streamable(self) -> strawberry.Streamable[str]:
        yield "a"
        yield "b"

    @strawberry.field
    async def dangerous_stream(self) -> strawberry.Streamable[str]:
        yield "safe"
        raise RuntimeError("Secret incremental stream error")

    @strawberry.field
    def deferred_payload(self) -> DeferredPayload:
        return DeferredPayload()


@pytest.mark.asyncio
async def test_stream_result_hook_wraps_each_subscription_result() -> None:
    events: list[str] = []

    class StreamModifierExtension(SchemaExtension):
        def on_stream_result(self, result: StreamExecutionResult) -> Iterator[None]:
            assert isinstance(result, ExecutionResult)
            assert result.data
            result.data["count"] += 10
            events.append("entered")
            try:
                yield
            finally:
                events.append("exited")

    schema = strawberry.Schema(
        query=Query,
        subscription=Subscription,
        extensions=[StreamModifierExtension],
    )

    results = await schema.stream("subscription { count }")
    try:
        first_result = await anext(results)
        assert isinstance(first_result, ExecutionResult)
        assert first_result.data == {"count": 11}
        assert events == ["entered"]

        second_result = await anext(results)
        assert isinstance(second_result, ExecutionResult)
        assert second_result.data == {"count": 12}
        assert events == ["entered", "exited", "entered"]
    finally:
        await results.aclose()

    assert events == ["entered", "exited", "entered", "exited"]


@pytest.mark.asyncio
async def test_async_stream_result_hook_wraps_query_result() -> None:
    events: list[str] = []

    class AsyncStreamModifierExtension(SchemaExtension):
        async def on_stream_result(
            self, result: StreamExecutionResult
        ) -> AsyncIterator[None]:
            await asyncio.sleep(0)
            assert isinstance(result, ExecutionResult)
            assert result.data
            result.data["hello"] = "modified"
            events.append("entered")
            try:
                yield
            finally:
                events.append("exited")

    schema = strawberry.Schema(
        query=Query,
        extensions=[AsyncStreamModifierExtension],
    )

    results = await schema.stream("{ hello }")
    try:
        result = await anext(results)
        assert isinstance(result, ExecutionResult)
        assert result.data == {"hello": "modified"}
        assert events == ["entered"]
    finally:
        await results.aclose()

    assert events == ["entered", "exited"]


@skip_if_gql_32("GraphQL 3.3.0 is required for incremental execution")
@pytest.mark.asyncio
async def test_stream_result_hook_wraps_incremental_delivery_frames() -> None:
    seen_results: list[StreamExecutionResult] = []

    class IncrementalModifierExtension(SchemaExtension):
        def on_stream_result(self, result: StreamExecutionResult) -> Iterator[None]:
            seen_results.append(result)
            result.extensions = {"hook": "called"}
            yield

    schema = strawberry.Schema(
        query=IncrementalQuery,
        extensions=[IncrementalModifierExtension],
        config=StrawberryConfig(enable_experimental_incremental_execution=True),
    )

    results = await schema.stream("{ streamable @stream }")
    frames = [frame async for frame in results]

    assert isinstance(frames[0], InitialIncrementalExecutionResult)
    assert all(
        isinstance(frame, SubsequentIncrementalExecutionResult) for frame in frames[1:]
    )
    assert seen_results == frames
    assert all(frame.extensions == {"hook": "called"} for frame in frames)


@pytest.mark.asyncio
async def test_stream_result_hook_is_not_called_by_execute() -> None:
    hook_called = False

    class MyExtension(SchemaExtension):
        def on_stream_result(self, result: StreamExecutionResult) -> Iterator[None]:
            nonlocal hook_called
            hook_called = True
            yield

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    result = await schema.execute("{ hello }")

    assert result.data == {"hello": "world"}
    assert not hook_called


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("operation", "secret"),
    [
        ("{ dangerousQuery }", "Secret query error"),
        ("mutation { dangerousMutation }", "Secret mutation error"),
    ],
)
async def test_mask_errors_before_streaming_query_or_mutation_result(
    operation: str, secret: str
) -> None:
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[MaskErrors],
    )

    results = await schema.stream(operation)
    try:
        result = await anext(results)
        assert isinstance(result, ExecutionResult)
        assert result.errors
        assert [error.message for error in result.errors] == ["Unexpected error."]
        assert all(secret not in error.message for error in result.errors)
    finally:
        await results.aclose()


@pytest.mark.asyncio
async def test_mask_errors_before_streaming_subscription_result() -> None:
    schema = strawberry.Schema(
        query=Query,
        subscription=Subscription,
        extensions=[MaskErrors],
    )

    results = await schema.stream("subscription { dangerousStream }")
    try:
        first_result = await anext(results)
        assert isinstance(first_result, ExecutionResult)
        assert first_result.data == {"dangerousStream": 1}

        error_result = await anext(results)
        assert isinstance(error_result, ExecutionResult)
        assert error_result.errors
        assert [error.message for error in error_result.errors] == ["Unexpected error."]
    finally:
        await results.aclose()


@skip_if_gql_32("GraphQL 3.3.0 is required for incremental execution")
@pytest.mark.asyncio
async def test_mask_errors_in_incremental_defer_result() -> None:
    schema = strawberry.Schema(
        query=IncrementalQuery,
        extensions=[MaskErrors],
        config=StrawberryConfig(enable_experimental_incremental_execution=True),
    )

    results = await schema.stream("{ deferredPayload { ... @defer { dangerous } } }")
    frames = [frame async for frame in results]
    errors = [
        error
        for frame in frames
        for incremental_result in getattr(frame, "incremental", None) or ()
        for error in incremental_result.errors or ()
    ]

    assert [error.message for error in errors] == ["Unexpected error."]


@skip_if_gql_32("GraphQL 3.3.0 is required for incremental execution")
@pytest.mark.asyncio
async def test_mask_errors_in_incremental_completed_result() -> None:
    schema = strawberry.Schema(
        query=IncrementalQuery,
        extensions=[MaskErrors],
        config=StrawberryConfig(enable_experimental_incremental_execution=True),
    )

    results = await schema.stream("{ dangerousStream @stream }")
    frames = [frame async for frame in results]
    errors = [
        error
        for frame in frames
        for completed_result in getattr(frame, "completed", None) or ()
        for error in completed_result.errors or ()
    ]

    assert [error.message for error in errors] == ["Unexpected error."]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    [
        "subscription { count",
        "{ missingField }",
        None,
    ],
)
async def test_mask_errors_before_streaming_pre_execution_error(
    operation: str | None,
) -> None:
    schema = strawberry.Schema(
        query=Query,
        subscription=Subscription,
        extensions=[MaskErrors],
    )

    results = await schema.stream(operation)
    try:
        result = await anext(results)
        assert isinstance(result, ExecutionResult)
        assert result.errors
        assert [error.message for error in result.errors] == ["Unexpected error."]
    finally:
        await results.aclose()
