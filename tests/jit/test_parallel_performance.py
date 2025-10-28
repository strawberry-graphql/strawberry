"""
Test and benchmark parallel async execution improvements.
"""

import asyncio
import time

from graphql import execute, parse

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class SlowAsyncType:
    """Type with multiple slow async fields to test parallelization."""

    id: str

    @strawberry.field
    async def field1(self) -> str:
        await asyncio.sleep(0.01)  # 10ms
        return f"field1-{self.id}"

    @strawberry.field
    async def field2(self) -> str:
        await asyncio.sleep(0.01)  # 10ms
        return f"field2-{self.id}"

    @strawberry.field
    async def field3(self) -> str:
        await asyncio.sleep(0.01)  # 10ms
        return f"field3-{self.id}"

    @strawberry.field
    async def field4(self) -> str:
        await asyncio.sleep(0.01)  # 10ms
        return f"field4-{self.id}"

    @strawberry.field
    async def field5(self) -> str:
        await asyncio.sleep(0.01)  # 10ms
        return f"field5-{self.id}"

    @strawberry.field
    def sync_field(self) -> str:
        return f"sync-{self.id}"


@strawberry.type
class Query:
    @strawberry.field
    async def slow_items(self, count: int = 3) -> list[SlowAsyncType]:
        await asyncio.sleep(0.01)
        return [SlowAsyncType(id=f"item{i}") for i in range(count)]

    @strawberry.field
    async def single_item(self) -> SlowAsyncType:
        await asyncio.sleep(0.01)
        return SlowAsyncType(id="single")


async def measure_execution_time(executor, iterations=5):
    """Measure average execution time over multiple iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        await executor()
        times.append(time.perf_counter() - start)
    return sum(times) / len(times)


async def benchmark_parallel_fields():
    """Benchmark queries with multiple parallel async fields."""
    schema = strawberry.Schema(Query)

    # Query with 5 async fields that could be parallelized
    query = """
    query ParallelFields {
        singleItem {
            id
            field1
            field2
            field3
            field4
            field5
            syncField
        }
    }
    """

    root = Query()

    # Standard GraphQL
    async def run_standard():
        return await execute(schema._schema, parse(query), root_value=root)

    std_time = await measure_execution_time(run_standard, 10)

    # Sequential JIT
    compiled_seq = compile_query(schema, query)

    async def run_sequential():
        return await compiled_seq(root)

    seq_time = await measure_execution_time(run_sequential, 10)

    # Parallel JIT
    compiled_par = compile_query(schema, query)

    async def run_parallel():
        return await compiled_par(root)

    par_time = await measure_execution_time(run_parallel, 10)

    # Theoretical minimum time (if all async fields run in parallel)
    # 1 async root field (10ms) + 5 parallel fields (10ms) = 20ms

    # Calculate speedup from parallelization
    if seq_time > par_time:
        pass

    return std_time, seq_time, par_time


async def benchmark_list_fields():
    """Benchmark queries with lists containing async fields."""
    schema = strawberry.Schema(Query)

    query = """
    query ListParallel {
        slowItems(count: 5) {
            id
            field1
            field2
            field3
            syncField
        }
    }
    """

    root = Query()

    # Standard GraphQL
    async def run_standard():
        return await execute(schema._schema, parse(query), root_value=root)

    std_time = await measure_execution_time(run_standard, 5)

    # Sequential JIT
    compiled_seq = compile_query(schema, query)

    async def run_sequential():
        return await compiled_seq(root)

    seq_time = await measure_execution_time(run_sequential, 5)

    # Parallel JIT
    compiled_par = compile_query(schema, query)

    async def run_parallel():
        return await compiled_par(root)

    par_time = await measure_execution_time(run_parallel, 5)

    # With perfect parallelization:
    # 1 root async (10ms) + 5 items * 3 fields in parallel (10ms) = 20ms per item
    # But items are processed sequentially, so: 10ms + (5 * 10ms) = 60ms theoretical

    if seq_time > par_time:
        pass

    return std_time, seq_time, par_time


async def benchmark_complex_query():
    """Benchmark a complex query with multiple levels."""
    schema = strawberry.Schema(Query)

    query = """
    query ComplexParallel {
        slowItems(count: 3) {
            id
            field1
            field2
            field3
            field4
            field5
        }
        item1: singleItem {
            id
            field1
            field2
        }
        item2: singleItem {
            id
            field3
            field4
        }
    }
    """

    root = Query()

    # Standard GraphQL
    async def run_standard():
        return await execute(schema._schema, parse(query), root_value=root)

    std_time = await measure_execution_time(run_standard, 5)

    # Sequential JIT
    compiled_seq = compile_query(schema, query)

    async def run_sequential():
        return await compiled_seq(root)

    seq_time = await measure_execution_time(run_sequential, 5)

    # Parallel JIT
    compiled_par = compile_query(schema, query)

    async def run_parallel():
        return await compiled_par(root)

    par_time = await measure_execution_time(run_parallel, 5)

    if seq_time > par_time:
        pass

    return std_time, seq_time, par_time


async def main():
    # Run benchmarks
    single_results = await benchmark_parallel_fields()
    list_results = await benchmark_list_fields()
    complex_results = await benchmark_complex_query()

    # Summary

    # Calculate average improvements
    (
        sum(
            [
                single_results[1] / single_results[2],
                list_results[1] / list_results[2],
                complex_results[1] / complex_results[2],
            ]
        )
        / 3
    )


if __name__ == "__main__":
    asyncio.run(main())
