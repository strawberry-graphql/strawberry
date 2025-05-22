import asyncio
from asyncio import sleep
from collections.abc import AsyncGenerator
from secrets import token_hex
from typing import Any, cast

from strawberry.http.async_base_view import AsyncBaseHTTPView


async def test_stream_with_heartbeat_should_always_yield_final_item() -> None:
    """
    Tests that AsyncBaseHTTPView._stream_with_heartbeat always yield the final item
    from a stream.

    This test creates a mock AsyncBaseHTTPView and verifies that when streaming data
    through the _stream_with_heartbeat method, the final item is always yielded in the
    output stream. It runs 100 concurrent tests to ensure reliability even with timing
    variations.
    """

    class MockAsyncBaseHTTPView:
        def encode_multipart_data(self, *_: Any, **__: Any) -> str:
            return ""

    view = MockAsyncBaseHTTPView()

    async def verify() -> None:
        final_item = token_hex(8)

        async def stream() -> AsyncGenerator[str, None]:
            yield ""
            yield final_item

        items = []
        async for item in AsyncBaseHTTPView._stream_with_heartbeat(
            cast("AsyncBaseHTTPView", view), stream, "graphql"
        )():
            items.append(item)
            await sleep(0.001)
        assert final_item in items

    await asyncio.gather(*(verify() for _ in range(100)))
