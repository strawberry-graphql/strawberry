import asyncio

import pytest
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
