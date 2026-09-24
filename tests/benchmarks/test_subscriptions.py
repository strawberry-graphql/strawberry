import asyncio
from contextlib import aclosing

import pytest
from pytest_codspeed import BenchmarkFixture

from .api import schema


@pytest.mark.benchmark_memory
def test_subscription_setup_and_close_v2(
    benchmark: BenchmarkFixture, benchmark_loop: asyncio.AbstractEventLoop
):
    async def run():
        results = []
        for _ in range(100):
            iterator = await schema.subscribe("subscription { something }")
            async with aclosing(iterator):
                results.append(await anext(iterator))
        return results

    results = benchmark(lambda: benchmark_loop.run_until_complete(run()))
    assert len(results) == 100
    for result in results:
        assert result.errors is None
        assert result.data == {"something": "Hello World!"}


@pytest.mark.parametrize(
    "count", [1000, pytest.param(20_000, marks=pytest.mark.benchmark_stress)]
)
def test_subscription_long_run_v2(
    benchmark: BenchmarkFixture, benchmark_loop: asyncio.AbstractEventLoop, count: int
):
    async def run():
        iterator = await schema.subscribe(
            "subscription ($count: Int!) { longRunning(count: $count) }",
            variable_values={"count": count},
        )
        async with aclosing(iterator):
            return [result async for result in iterator]

    results = benchmark(lambda: benchmark_loop.run_until_complete(run()))
    assert len(results) == count
    for i, result in enumerate(results):
        assert result.errors is None
        assert result.data == {"longRunning": i}
