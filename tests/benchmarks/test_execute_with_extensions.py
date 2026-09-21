import asyncio
from inspect import isawaitable
from pathlib import Path
from typing import Any

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

import strawberry
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue

from .api import Query
from .assertions import assert_items


class SimpleExtension(SchemaExtension):
    def get_results(self) -> AwaitableOrValue[dict[str, Any]]:
        return super().get_results()


class ResolveExtension(SchemaExtension):
    async def resolve(self, _next, root, info, *args: Any, **kwargs: Any) -> Any:
        result = _next(root, info, *args, **kwargs)
        if isawaitable(result):
            result = await result
        return result


ROOT = Path(__file__).parent / "queries"

items_query = (ROOT / "items.graphql").read_text()


@pytest.mark.benchmark
@pytest.mark.parametrize("items", [1_000, 10_000], ids=lambda x: f"items_{x}")
@pytest.mark.parametrize(
    "extensions",
    [[], [SimpleExtension], [ResolveExtension]],
    ids=lambda x: (
        f"with_{'_'.join(ext.__name__.lower() for ext in x) or 'no_extensions'}"
    ),
)
def test_execute_v2(
    benchmark: BenchmarkFixture,
    items: int,
    extensions: list[type[SchemaExtension]],
    benchmark_loop: asyncio.AbstractEventLoop,
):
    schema = strawberry.Schema(query=Query, extensions=extensions)

    def run():
        return benchmark_loop.run_until_complete(
            schema.execute(items_query, variable_values={"count": items})
        )

    results = benchmark(run)

    assert_items(results, items)
