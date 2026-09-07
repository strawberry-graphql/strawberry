import asyncio

import pytest
from pytest_codspeed import BenchmarkFixture

import strawberry

from .api import Item
from .assertions import assert_items


@pytest.mark.parametrize("count", [1, 1000])
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_matched_resolvers(
    benchmark: BenchmarkFixture,
    benchmark_loop: asyncio.AbstractEventLoop,
    count: int,
    asynchronous: bool,
):
    items = [Item(name="Item", index=i) for i in range(count)]

    def resolve() -> list[Item]:
        return items

    async def resolve_async() -> list[Item]:
        await asyncio.sleep(0)
        return items

    query = strawberry.type(
        type(
            "Query",
            (),
            {
                "items": strawberry.field(
                    resolver=resolve_async if asynchronous else resolve
                )
            },
        )
    )
    schema = strawberry.Schema(query=query)
    operation = "{ items { name index } }"

    def run():
        if asynchronous:
            return benchmark_loop.run_until_complete(schema.execute(operation))
        return schema.execute_sync(operation)

    assert_items(benchmark(run), count)
