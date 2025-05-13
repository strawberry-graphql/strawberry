import asyncio
from collections.abc import AsyncIterator

import pytest
from graphql import ExecutionResult
from pytest_codspeed.plugin import BenchmarkFixture

from .api import schema


@pytest.mark.benchmark
def test_subscription(benchmark: BenchmarkFixture):
    s = """
    subscription {
        something
    }
    """

    async def _run():
        for _ in range(100):
            iterator = await schema.subscribe(s)

            value = await iterator.__anext__()  # type: ignore[union-attr]

            assert value.data is not None
            assert value.data["something"] == "Hello World!"

    benchmark(lambda: asyncio.run(_run()))


@pytest.mark.benchmark
@pytest.mark.parametrize("count", [1000, 20000])
def test_subscription_long_run(benchmark: BenchmarkFixture, count: int) -> None:
    s = """#graphql
    subscription LongRunning($count: Int!) {
        longRunning(count: $count)
    }
    """

    async def _run():
        i = 0
        aiterator: AsyncIterator[ExecutionResult] = await schema.subscribe(
            s, variable_values={"count": count}
        )  # type: ignore[assignment]
        async for res in aiterator:
            assert res.data is not None
            assert res.data["longRunning"] == i
            i += 1

    benchmark(lambda: asyncio.run(_run()))
