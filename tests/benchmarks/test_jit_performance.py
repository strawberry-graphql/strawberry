"""Benchmarks comparing JIT compiler performance vs standard execution.

This benchmark suite measures:
1. Stadium benchmark - Large nested dataset (45k-90k seats)
2. Simple query - Baseline performance
3. Async query - Parallel execution performance
4. Compilation overhead - First vs cached compilation

Uses pytest-codspeed for tracking performance over time.
"""

import asyncio
from pathlib import Path

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

import strawberry
from strawberry.jit import compile_query

# Import stadium types from existing benchmark
from .test_stadium import (
    Query as StadiumQuery,
)

ROOT = Path(__file__).parent / "queries"
stadium_query = (ROOT / "stadium.graphql").read_text()


@pytest.mark.benchmark
@pytest.mark.parametrize("seats_per_row", [250], ids=lambda x: f"seats_per_row_{x}")
def test_jit_stadium_vs_standard(benchmark: BenchmarkFixture, seats_per_row: int):
    """Benchmark JIT vs standard execution on stadium query (~45k seats).

    This is the key performance benchmark comparing:
    - Standard GraphQL execution (baseline)
    - JIT compiled execution (optimized)

    Expected result: JIT should be 5-8x faster than standard.
    """
    schema = strawberry.Schema(query=StadiumQuery)

    # Pre-compile the query (compilation time not included in benchmark)
    compiled_fn = compile_query(schema, stadium_query)
    root = StadiumQuery()

    def run():
        return compiled_fn(root, variables={"seatsPerRow": seats_per_row})

    results = benchmark(run)

    assert results["data"] is not None
    assert results["data"]["stadium"]["name"] == "Grand Metropolitan Stadium"


@pytest.mark.benchmark
@pytest.mark.parametrize("seats_per_row", [250], ids=lambda x: f"seats_per_row_{x}")
def test_standard_stadium_baseline(benchmark: BenchmarkFixture, seats_per_row: int):
    """Baseline benchmark for standard GraphQL execution on stadium query.

    This provides the baseline to compare JIT performance against.
    Run both this and test_jit_stadium_vs_standard to see speedup.
    """
    schema = strawberry.Schema(query=StadiumQuery)

    def run():
        return asyncio.run(
            schema.execute(
                stadium_query, variable_values={"seatsPerRow": seats_per_row}
            )
        )

    results = benchmark(run)

    assert results.errors is None
    assert results.data is not None
    assert results.data["stadium"]["name"] == "Grand Metropolitan Stadium"


# Async parallel execution benchmark
@strawberry.type
class AsyncQuery:
    @strawberry.field
    async def field1(self) -> str:
        """Simulates async DB query."""
        await asyncio.sleep(0.001)
        return "field1"

    @strawberry.field
    async def field2(self) -> str:
        """Simulates async DB query."""
        await asyncio.sleep(0.001)
        return "field2"

    @strawberry.field
    async def field3(self) -> str:
        """Simulates async DB query."""
        await asyncio.sleep(0.001)
        return "field3"

    @strawberry.field
    async def field4(self) -> str:
        """Simulates async DB query."""
        await asyncio.sleep(0.001)
        return "field4"

    @strawberry.field
    async def field5(self) -> str:
        """Simulates async DB query."""
        await asyncio.sleep(0.001)
        return "field5"


@pytest.mark.benchmark
def test_jit_parallel_async(benchmark: BenchmarkFixture):
    """Benchmark JIT parallel async execution (5 concurrent async fields).

    This demonstrates the parallel execution optimization where independent
    async fields run concurrently using asyncio.gather().

    Expected: ~1ms (all 5 fields run in parallel) vs 5ms (sequential)
    """
    schema = strawberry.Schema(query=AsyncQuery)

    query = """
    {
        field1
        field2
        field3
        field4
        field5
    }
    """

    compiled_fn = compile_query(schema, query)
    root = AsyncQuery()

    async def run():
        return await compiled_fn(root)

    results = benchmark(lambda: asyncio.run(run()))

    assert results["data"]["field1"] == "field1"
    assert results["data"]["field5"] == "field5"


@pytest.mark.benchmark
def test_standard_async_baseline(benchmark: BenchmarkFixture):
    """Baseline for standard async execution (sequential).

    Standard GraphQL execution runs async fields sequentially.
    Compare with test_jit_parallel_async to see parallel speedup.
    """
    schema = strawberry.Schema(query=AsyncQuery)

    query = """
    {
        field1
        field2
        field3
        field4
        field5
    }
    """

    def run():
        return asyncio.run(schema.execute(query, root_value=AsyncQuery()))

    results = benchmark(run)

    assert results.errors is None
    assert results.data["field1"] == "field1"


# Simple query benchmark
@strawberry.type
class SimpleQuery:
    @strawberry.field
    def user(self, id: int) -> str:
        return f"User {id}"

    @strawberry.field
    def posts(self, limit: int) -> list[str]:
        return [f"Post {i}" for i in range(limit)]


@pytest.mark.benchmark
def test_jit_simple_query(benchmark: BenchmarkFixture):
    """Benchmark JIT on a simple query (baseline overhead test)."""
    schema = strawberry.Schema(query=SimpleQuery)

    query = """
    {
        user(id: 1)
        posts(limit: 10)
    }
    """

    compiled_fn = compile_query(schema, query)
    root = SimpleQuery()

    def run():
        return compiled_fn(root)

    results = benchmark(run)

    assert results["data"]["user"] == "User 1"
    assert len(results["data"]["posts"]) == 10


@pytest.mark.benchmark
def test_standard_simple_query(benchmark: BenchmarkFixture):
    """Baseline for simple query with standard execution."""
    schema = strawberry.Schema(query=SimpleQuery)

    query = """
    {
        user(id: 1)
        posts(limit: 10)
    }
    """

    def run():
        return asyncio.run(schema.execute(query, root_value=SimpleQuery()))

    results = benchmark(run)

    assert results.errors is None
    assert results.data["user"] == "User 1"


# Compilation overhead benchmarks
@pytest.mark.benchmark
def test_jit_compilation_time(benchmark: BenchmarkFixture):
    """Benchmark the compilation time itself (cold start).

    This measures how long it takes to compile a query from scratch.
    Important for understanding first-request latency.
    """
    schema = strawberry.Schema(query=StadiumQuery)

    def run():
        # Compile a fresh query each time
        return compile_query(schema, stadium_query)

    compiled_fn = benchmark(run)

    # Verify it works
    root = StadiumQuery()
    result = compiled_fn(root, variables={"seatsPerRow": 50})
    assert result["data"] is not None


@pytest.mark.benchmark
def test_jit_cached_compilation(benchmark: BenchmarkFixture):
    """Benchmark cached compilation (with manual cache).

    This demonstrates how users can implement their own cache.
    """
    schema = strawberry.Schema(query=StadiumQuery)

    # Simple manual cache
    query_cache = {}

    def get_compiled(query: str):
        if query not in query_cache:
            query_cache[query] = compile_query(schema, query)
        return query_cache[query]

    # Prime the cache
    get_compiled(stadium_query)

    def run():
        # This should hit the cache
        return get_compiled(stadium_query)

    compiled_fn = benchmark(run)

    # Verify it works
    root = StadiumQuery()
    result = compiled_fn(root, variables={"seatsPerRow": 50})
    assert result["data"] is not None


# Large result set benchmark
@pytest.mark.benchmark
@pytest.mark.parametrize("seats_per_row", [500], ids=lambda x: f"seats_per_row_{x}")
def test_jit_large_dataset(benchmark: BenchmarkFixture, seats_per_row: int):
    """Benchmark JIT with very large dataset (~90k seats).

    Tests performance scaling with 2x data volume.
    """
    schema = strawberry.Schema(query=StadiumQuery)
    compiled_fn = compile_query(schema, stadium_query)
    root = StadiumQuery()

    def run():
        return compiled_fn(root, variables={"seatsPerRow": seats_per_row})

    results = benchmark(run)

    assert results["data"] is not None
    assert len(results["data"]["stadium"]["stands"]) == 4
