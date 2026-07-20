import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Iterator

import pytest

import strawberry
from strawberry.extensions import MaskErrors, SchemaExtension
from strawberry.types import ExecutionResult


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


@pytest.mark.asyncio
async def test_stream_result_hook_wraps_each_subscription_result() -> None:
    events: list[str] = []

    class StreamModifierExtension(SchemaExtension):
        def on_stream_result(self, result: ExecutionResult) -> Iterator[None]:
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
            self, result: ExecutionResult
        ) -> AsyncIterator[None]:
            await asyncio.sleep(0)
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


@pytest.mark.asyncio
async def test_stream_result_hook_is_not_called_by_execute() -> None:
    hook_called = False

    class MyExtension(SchemaExtension):
        def on_stream_result(self, result: ExecutionResult) -> Iterator[None]:
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
