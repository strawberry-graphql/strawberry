import asyncio

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

from strawberry.dataloader import DataLoader


async def load_values(keys: list[int]) -> list[int]:
    # Yield like an async database driver, without artificial I/O latency.
    await asyncio.sleep(0)
    return keys


async def load_many_values(count: int, cache: bool) -> list[int]:
    loader = DataLoader(load_fn=load_values, cache=cache)
    return await loader.load_many(range(count))


@pytest.mark.benchmark
@pytest.mark.parametrize("count", [1, 10, 100, 10_000])
@pytest.mark.parametrize("cache", [False, True])
def test_dataloader_batch(benchmark: BenchmarkFixture, count: int, cache: bool):
    def run() -> list[int]:
        return asyncio.run(load_many_values(count, cache))

    assert benchmark(run) == list(range(count))
