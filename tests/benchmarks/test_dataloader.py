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
def test_dataloader_batch_v2(
    benchmark: BenchmarkFixture,
    count: int,
    cache: bool,
    benchmark_loop: asyncio.AbstractEventLoop,
):
    def run() -> list[int]:
        return benchmark_loop.run_until_complete(load_many_values(count, cache))

    assert benchmark(run) == list(range(count))


@pytest.mark.parametrize("cache", [False, True], ids=["uncached", "cached"])
@pytest.mark.parametrize(
    "repeat", [False, True], ids=["duplicate_keys", "second_batch"]
)
def test_dataloader_cache_semantics(
    benchmark: BenchmarkFixture,
    benchmark_loop: asyncio.AbstractEventLoop,
    cache: bool,
    repeat: bool,
):
    async def run():
        calls = []

        async def load(keys: list[int]) -> list[int]:
            calls.append(list(keys))
            await asyncio.sleep(0)
            return keys

        loader = DataLoader(load_fn=load, cache=cache)
        keys = list(range(100)) if repeat else [i // 2 for i in range(100)]
        values = await loader.load_many(keys)
        if repeat:
            values = await loader.load_many(keys)
        return values, calls

    values, calls = benchmark(lambda: benchmark_loop.run_until_complete(run()))
    expected = list(range(100)) if repeat else [i // 2 for i in range(100)]
    assert values == expected
    assert len(calls) == (2 if repeat and not cache else 1)
    assert calls[0] == (list(range(50)) if cache and not repeat else expected)
