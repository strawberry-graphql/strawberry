import asyncio
from asyncio import sleep
from collections import Counter
from collections.abc import AsyncGenerator
from random import random

import pytest

from strawberry.http.streaming import merge_stream_with_heartbeat


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
    Verifies merge_stream_with_heartbeat delivers all items in correct order.

    Tests three critical stream properties:
    1. Completeness: All source items appear in output (especially the last item)
    2. Uniqueness: Each expected item appears exactly once
    3. Order: Original sequence of items is preserved

    Uses multiple test cases via parametrization and runs 100 concurrent streams
    with randomized delays to stress-test the implementation. This specifically
    targets race conditions between the drain task and queue consumer that could
    cause missing items, duplicates, or reordering.
    """

    assert len(set(expected)) == len(expected), "Test requires unique elements"

    async def stream() -> AsyncGenerator[str, None]:
        for elem in expected:
            yield elem

    merged_stream = merge_stream_with_heartbeat(
        stream,
        heartbeat_message=lambda: "heartbeat",
        interval=60,
        send_initial_heartbeat=False,
    )

    async def collect() -> list[str]:
        result = []
        async for item in merged_stream():
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


async def test_stream_with_heartbeat_uses_heartbeat_message() -> None:
    async def stream() -> AsyncGenerator[str, None]:
        await sleep(0)
        yield "last"

    result = [
        item
        async for item in merge_stream_with_heartbeat(
            stream,
            lambda: "heartbeat",
            interval=60,
            send_initial_heartbeat=True,
        )()
    ]

    assert "heartbeat" in result
    assert "last" in result
