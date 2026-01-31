"""
Tests for subscription race condition in AsyncBaseHTTPView._stream_with_heartbeat.

## The Race Condition

In `_stream_with_heartbeat`, the `merged()` async generator checks `while not task.done()`
before calling `await queue.get()`. If the drain task completes (making `task.done()` True)
after queueing the final boundary but before `queue.get()` retrieves it, the while loop exits
immediately and the final multipart boundary (`--graphql--\r\n`) is never yielded to the client.

This causes malformed multipart responses that violate RFC 2046, leading to clients waiting
until timeout and unpredictable behavior across different client implementations.

## Test Strategy

Since the race is non-deterministic and timing-dependent, we use `MockRacyAsyncGenerator`
to simulate the race by wrapping the `stream()` function passed to `_stream_with_heartbeat`.
The mock intercepts chunks from the stream and drops the final boundary chunk by raising
`StopAsyncIteration` when it sees `--graphql--`. This simulates the closing boundary being
lost before it can be added to the internal queue, which is functionally equivalent to the
race where it's queued but not retrieved before the loop exits.

The test patches `_stream_with_heartbeat` to inject the mock wrapper around the input stream,
ensuring the race is simulated at the correct layer
"""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

import pytest

import strawberry
from strawberry.http.async_base_view import AsyncBaseHTTPView
from tests.http.clients.base import HttpClient

# Constants
GRAPHQL_BOUNDARY_CLOSING = "--graphql--"


@strawberry.type
class Query:
    @strawberry.field
    def test(self) -> str:
        return "test"


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def quick_count(self, target: int = 2) -> AsyncGenerator[int, None]:
        """Fast subscription that completes quickly."""
        for i in range(target):
            yield i


@pytest.fixture
def subscription_schema():
    """Schema with a simple subscription for race condition testing."""
    return strawberry.Schema(
        query=Query,
        subscription=Subscription,
    )


class MockRacyAsyncGenerator:
    """
    Simulates the race condition by dropping the final boundary chunk.

    Wraps the stream() generator passed to _stream_with_heartbeat and intercepts
    the final boundary chunk. When the closing boundary is detected, raises
    StopAsyncIteration instead of yielding it. This simulates the boundary being
    lost before it enters the internal queue in merged(), which is functionally
    equivalent to the race where it's queued but not retrieved before the loop exits.
    """

    def __init__(self, real_generator: AsyncGenerator[str, None]):
        self.real_generator = real_generator
        self.chunks: list[str] = []

    def __aiter__(self) -> "MockRacyAsyncGenerator":
        return self

    async def __anext__(self) -> str:
        chunk = await self.real_generator.__anext__()
        self.chunks.append(chunk)

        # Simulate the race: drop the closing boundary by raising StopAsyncIteration
        # This prevents it from being added to the queue in merged()
        if GRAPHQL_BOUNDARY_CLOSING in chunk:
            raise StopAsyncIteration

        return chunk

    async def aclose(self) -> None:
        await self.real_generator.aclose()

    async def asend(self, value: Any) -> str:  # pragma: no cover
        return await self.real_generator.asend(value)

    async def athrow(
        self, typ: Any, val: Any = None, tb: Any = None
    ) -> str:  # pragma: no cover
        return await self.real_generator.athrow(typ, val, tb)


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["get", "post"])
async def test_subscription_race_condition_missing_boundary(
    incremental_http_client_class: type[HttpClient],
    subscription_schema: strawberry.Schema,
    method: str,
):
    """
    Test that demonstrates the race condition where the final boundary is lost.

    Uses MockRacyAsyncGenerator to simulate the race where the stream() generator
    completes after yielding the closing boundary, but the boundary gets stuck in
    the queue when task.done() becomes True before the final queue.get().
    """
    http_client = incremental_http_client_class(schema=subscription_schema)

    original_stream_with_heartbeat = AsyncBaseHTTPView._stream_with_heartbeat

    def patched_stream_with_heartbeat(self, stream_fn, separator):
        # Wrap the stream function to simulate the race
        def wrapped_stream_fn():
            original_stream = stream_fn()
            return MockRacyAsyncGenerator(original_stream)

        # Call the original _stream_with_heartbeat with our wrapped stream
        return original_stream_with_heartbeat(self, wrapped_stream_fn, separator)

    with patch.object(
        AsyncBaseHTTPView, "_stream_with_heartbeat", patched_stream_with_heartbeat
    ):
        response = await http_client.query(
            method=method,
            query="subscription { quickCount(target: 2) }",
            headers={
                "accept": "multipart/mixed;boundary=graphql;subscriptionSpec=1.0,application/json",
                "content-type": "application/json",
            },
        )

    assert response.status_code == 200

    full_response = response.text

    parts = full_response.split("--graphql")
    assert len(parts) >= 3, (
        f"Expected at least 3 multipart sections (2 data chunks + final boundary), "
        f"got {len(parts)}\n"
        f"Full response:\n{full_response}"
    )

    assert full_response.rstrip().endswith(GRAPHQL_BOUNDARY_CLOSING), (
        f"Response must end with closing boundary {GRAPHQL_BOUNDARY_CLOSING}\n"
        f"Full response:\n{full_response}"
    )
