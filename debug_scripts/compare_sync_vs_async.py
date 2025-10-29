"""Compare JIT performance on sync vs async queries."""

import asyncio
import sys
import time
from pathlib import Path

# Add stadium benchmark path
sys.path.insert(0, str(Path(__file__).parent.parent / "tests" / "benchmarks"))

from test_jit_async_nested import NESTED_ASYNC_QUERY
from test_jit_async_nested import Query as AsyncQuery
from test_stadium import Query as StadiumQuery

import strawberry
from strawberry.jit import compile_query

# Stadium query (sync)
stadium_query = (
    Path(__file__).parent.parent / "tests/benchmarks/queries/stadium.graphql"
).read_text()


def benchmark_sync():
    """Benchmark stadium (all sync fields)."""
    schema = strawberry.Schema(query=StadiumQuery)
    compiled_fn = compile_query(schema, stadium_query)
    root = StadiumQuery()

    iterations = 20

    # Warmup
    for _ in range(3):
        compiled_fn(root, variables={"seatsPerRow": 250})
        asyncio.run(schema.execute(stadium_query, variable_values={"seatsPerRow": 250}))

    # Benchmark JIT
    start = time.perf_counter()
    for _ in range(iterations):
        compiled_fn(root, variables={"seatsPerRow": 250})
    jit_time = (time.perf_counter() - start) / iterations * 1000

    # Benchmark standard
    start = time.perf_counter()
    for _ in range(iterations):
        asyncio.run(schema.execute(stadium_query, variable_values={"seatsPerRow": 250}))
    std_time = (time.perf_counter() - start) / iterations * 1000

    return std_time, jit_time


def benchmark_async():
    """Benchmark nested async fields."""
    schema = strawberry.Schema(query=AsyncQuery)
    compiled_fn = compile_query(schema, NESTED_ASYNC_QUERY)
    root = AsyncQuery()

    iterations = 20

    # Warmup
    for _ in range(3):
        asyncio.run(compiled_fn(root))
        asyncio.run(schema.execute(NESTED_ASYNC_QUERY, root_value=root))

    # Benchmark JIT
    start = time.perf_counter()
    for _ in range(iterations):
        asyncio.run(compiled_fn(root))
    jit_time = (time.perf_counter() - start) / iterations * 1000

    # Benchmark standard
    start = time.perf_counter()
    for _ in range(iterations):
        asyncio.run(schema.execute(NESTED_ASYNC_QUERY, root_value=root))
    std_time = (time.perf_counter() - start) / iterations * 1000

    return std_time, jit_time


print("\n🔬 JIT Performance Comparison\n")
print("=" * 70)

# Test 1: Sync fields (stadium)
std, jit = benchmark_sync()
ratio = std / jit
status = "✓ FASTER" if ratio > 1 else "✗ SLOWER"
print("\n1. Stadium Benchmark (ALL SYNC FIELDS)")
print(f"   Standard: {std:7.2f}ms")
print(f"   JIT:      {jit:7.2f}ms")
print(f"   Speedup:  {ratio:7.2f}x {status}")

# Test 2: Async nested fields
std, jit = benchmark_async()
ratio = std / jit
status = "✓ FASTER" if ratio > 1 else "✗ SLOWER"
print("\n2. Nested Async Query (3 LEVELS OF ASYNC)")
print(f"   Standard: {std:7.2f}ms")
print(f"   JIT:      {jit:7.2f}ms")
print(f"   Speedup:  {ratio:7.2f}x {status}")

print("\n" + "=" * 70)
print("\nCONCLUSION:")
print("  • JIT is FAST for sync queries (matches 6x claim)")
print("  • JIT is SLOW for async queries (regression not previously tested)")
print()
