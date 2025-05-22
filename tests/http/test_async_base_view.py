import asyncio
from asyncio import sleep
from collections import Counter
from collections.abc import AsyncGenerator
from random import random
from typing import Any, cast

import pytest

from strawberry.http.async_base_view import AsyncBaseHTTPView


@pytest.mark.parametrize(
    "expected",
    [
        pytest.param(["last"], id="single_item"),
        pytest.param(["1st", "last"], id="two_items"),
        pytest.param(["1st", "2nd", "last"], id="three_items"),
    ],
)
async def test_stream_with_heartbeat_should_yield_items_correctly(
    expected: list[str],
) -> None:
    """
    Verifies that _stream_with_heartbeat correctly processes all stream items.

    Ensures three key requirements are met:
    1. Completeness: All items from the source stream appear in the output
    2. Uniqueness: Each expected item appears exactly once (no duplicates)
    3. Order: Original sequence of items is preserved

    Uses parametrization to test various input sizes and runs 100 concurrent
    streams with randomized delays to detect potential race conditions between the
    drain task and queue consumer that might affect item delivery or ordering.
    """

    assert len(set(expected)) == len(expected), "Test requires unique elements"

    class MockAsyncBaseHTTPView:
        def encode_multipart_data(self, *_: Any, **__: Any) -> str:
            return ""

    view = MockAsyncBaseHTTPView()

    async def stream() -> AsyncGenerator[str, None]:
        for elem in expected:
            yield elem

    async def collect() -> list[str]:
        result = []
        async for item in AsyncBaseHTTPView._stream_with_heartbeat(
            cast("AsyncBaseHTTPView", view), stream, ""
        )():
            result.append(item)
            # Random sleep to promote race conditions between concurrent tasks
            await sleep(random() / 1000)  # noqa: S311
        return result

    for actual in await asyncio.gather(*(collect() for _ in range(100))):
        # Validation 1: Item completeness
        count = Counter(actual)
        if missing_items := set(expected) - set(count):
            assert not missing_items, f"Missing expected items: {list(missing_items)}"

        # Validation 2: No duplicates
        for item in expected:
            item_count = count[item]
            assert item_count == 1, (
                f"Expected item '{item}' appears {item_count} times (should appear exactly once)"
            )

        # Validation 3: Preserved ordering
        item_indices = {item: actual.index(item) for item in expected}
        for i in range(len(expected) - 1):
            curr, next_item = expected[i], expected[i + 1]
            assert item_indices[curr] < item_indices[next_item], (
                f"Order incorrect: '{curr}' (at index {item_indices[curr]}) "
                f"should appear before '{next_item}' (at index {item_indices[next_item]})"
            )
