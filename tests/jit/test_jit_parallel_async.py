"""
Test parallel async execution in JIT compiler.
"""

import asyncio
import time
from pathlib import Path
from typing import List

import pytest
from graphql import execute, parse
from pytest_snapshot.plugin import Snapshot

import strawberry
from strawberry.jit_compiler import compile_query
from strawberry.jit_compiler_parallel import (
    ParallelAsyncJITCompiler,
    compile_query_parallel,
)

HERE = Path(__file__).parent


@strawberry.type
class Author:
    id: str
    name: str

    @strawberry.field
    async def bio(self) -> str:
        """Simulate slow async field."""
        await asyncio.sleep(0.01)  # 10ms delay
        return f"Bio of {self.name}"

    @strawberry.field
    async def email(self) -> str:
        """Another slow async field."""
        await asyncio.sleep(0.01)  # 10ms delay
        return f"{self.name.lower()}@example.com"

    @strawberry.field
    async def website(self) -> str:
        """Third slow async field."""
        await asyncio.sleep(0.01)  # 10ms delay
        return f"https://{self.name.lower()}.com"

    @strawberry.field
    def sync_field(self) -> str:
        """Fast sync field."""
        return "sync"


@strawberry.type
class Post:
    id: str
    title: str

    def __init__(self, id: str, title: str):
        self.id = id
        self.title = title
        self._author = Author(id="a1", name="Alice")

    @strawberry.field
    async def content(self) -> str:
        """Slow async field."""
        await asyncio.sleep(0.01)  # 10ms delay
        return f"Content for {self.title}"

    @strawberry.field
    async def author(self) -> Author:
        """Slow async field returning object."""
        await asyncio.sleep(0.01)  # 10ms delay
        return self._author

    @strawberry.field
    async def view_count(self) -> int:
        """Another slow async field."""
        await asyncio.sleep(0.01)  # 10ms delay
        return 100

    @strawberry.field
    async def likes(self) -> int:
        """Another slow async field."""
        await asyncio.sleep(0.01)  # 10ms delay
        return 50

    @strawberry.field
    def word_count(self) -> int:
        """Fast sync field."""
        return 10


@strawberry.type
class Query:
    @strawberry.field
    async def posts(self, limit: int = 3) -> List[Post]:
        """Async resolver returning posts."""
        await asyncio.sleep(0.01)  # 10ms delay
        return [Post(id=f"p{i}", title=f"Post {i}") for i in range(limit)]

    @strawberry.field
    async def featured_post(self) -> Post:
        """Another async field."""
        await asyncio.sleep(0.01)  # 10ms delay
        return Post(id="featured", title="Featured Post")

    @strawberry.field
    async def trending_post(self) -> Post:
        """Another async field."""
        await asyncio.sleep(0.01)  # 10ms delay
        return Post(id="trending", title="Trending Post")

    @strawberry.field
    def sync_posts(self) -> List[Post]:
        """Sync resolver."""
        return [Post(id="s1", title="Sync Post")]


@pytest.mark.asyncio
async def test_parallel_execution_simple():
    """Test that parallel execution works for simple async fields."""
    schema = strawberry.Schema(Query)

    # Query with multiple async fields at the same level
    query = """
    query ParallelTest {
        posts {
            id
            title
        }
        featuredPost {
            id
            title
        }
        trendingPost {
            id
            title
        }
    }
    """

    # Sequential execution (standard JIT)
    compiled_sequential = compile_query(schema._schema, query)
    root = Query()

    start = time.perf_counter()
    result_seq = await compiled_sequential(root)
    sequential_time = time.perf_counter() - start

    # Parallel execution
    compiled_parallel = compile_query_parallel(schema._schema, query)

    start = time.perf_counter()
    result_par = await compiled_parallel(root)
    parallel_time = time.perf_counter() - start

    # Results should be identical
    assert result_seq == result_par

    # Parallel should be faster (3 fields * 10ms = 30ms sequential vs ~10ms parallel)
    print("\n📊 Simple Parallel Test:")
    print(f"  Sequential: {sequential_time * 1000:.2f}ms")
    print(f"  Parallel:   {parallel_time * 1000:.2f}ms")
    print(f"  Speedup:    {sequential_time / parallel_time:.2f}x")

    # Parallel should be at least 2x faster for 3 parallel fields
    assert parallel_time < sequential_time * 0.6


@pytest.mark.asyncio
async def test_parallel_execution_nested():
    """Test parallel execution with nested async fields."""
    schema = strawberry.Schema(Query)

    # Query with nested async fields
    query = """
    query NestedParallel {
        posts {
            id
            content
            viewCount
            likes
            author {
                bio
                email
                website
            }
        }
    }
    """

    # Sequential execution
    compiled_sequential = compile_query(schema._schema, query)
    root = Query()

    start = time.perf_counter()
    result_seq = await compiled_sequential(root)
    sequential_time = time.perf_counter() - start

    # Parallel execution
    compiled_parallel = compile_query_parallel(schema._schema, query)

    start = time.perf_counter()
    result_par = await compiled_parallel(root)
    parallel_time = time.perf_counter() - start

    # Results should be identical
    assert result_seq == result_par

    print("\n📊 Nested Parallel Test:")
    print(f"  Sequential: {sequential_time * 1000:.2f}ms")
    print(f"  Parallel:   {parallel_time * 1000:.2f}ms")
    print(f"  Speedup:    {sequential_time / parallel_time:.2f}x")

    # Should show improvement from parallel execution
    assert parallel_time < sequential_time


@pytest.mark.asyncio
async def test_parallel_execution_mixed():
    """Test parallel execution with mixed sync/async fields."""
    schema = strawberry.Schema(Query)

    query = """
    query MixedParallel {
        posts {
            id
            wordCount
            content
            viewCount
            likes
        }
        syncPosts {
            id
            wordCount
        }
        featuredPost {
            id
            content
        }
    }
    """

    # Sequential execution
    compiled_sequential = compile_query(schema._schema, query)
    root = Query()

    start = time.perf_counter()
    result_seq = await compiled_sequential(root)
    sequential_time = time.perf_counter() - start

    # Parallel execution
    compiled_parallel = compile_query_parallel(schema._schema, query)

    start = time.perf_counter()
    result_par = await compiled_parallel(root)
    parallel_time = time.perf_counter() - start

    # Results should be identical
    assert result_seq == result_par

    print("\n📊 Mixed Sync/Async Test:")
    print(f"  Sequential: {sequential_time * 1000:.2f}ms")
    print(f"  Parallel:   {parallel_time * 1000:.2f}ms")
    print(f"  Speedup:    {sequential_time / parallel_time:.2f}x")


@pytest.mark.asyncio
async def test_parallel_execution_snapshot(snapshot: Snapshot):
    """Test that parallel execution generates correct code."""
    schema = strawberry.Schema(Query)

    query = """
    query ParallelSnapshot {
        posts {
            id
            content
            viewCount
        }
        featuredPost {
            id
            content
        }
    }
    """

    # Generate code with parallel compiler
    compiler = ParallelAsyncJITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    generated_code = compiler._generate_function(operation, root_type)

    # Check snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_parallel"
    snapshot.assert_match(generated_code, "parallel_async_query.py")

    # Execute and verify
    compiled_fn = compile_query_parallel(schema._schema, query)
    root = Query()

    result = await compiled_fn(root)

    assert len(result["posts"]) == 3
    assert result["posts"][0]["content"] == "Content for Post 0"
    assert result["featuredPost"]["id"] == "featured"


@pytest.mark.asyncio
async def benchmark_parallel_performance():
    """Benchmark the performance improvement from parallel execution."""
    schema = strawberry.Schema(Query)

    # Query with many parallel async fields
    query = """
    query BenchmarkParallel {
        posts(limit: 5) {
            id
            title
            content
            viewCount
            likes
            author {
                name
                bio
                email
                website
            }
        }
        featuredPost {
            id
            content
            viewCount
            author {
                bio
                email
            }
        }
        trendingPost {
            id
            content
            likes
        }
    }
    """

    root = Query()

    # Warmup
    for _ in range(3):
        await execute(schema._schema, parse(query), root_value=root)

    # Standard GraphQL execution
    start = time.perf_counter()
    for _ in range(5):
        result = await execute(schema._schema, parse(query), root_value=root)
    standard_time = time.perf_counter() - start

    # Sequential JIT
    compiled_seq = compile_query(schema._schema, query)
    start = time.perf_counter()
    for _ in range(5):
        result = await compiled_seq(root)
    sequential_time = time.perf_counter() - start

    # Parallel JIT
    compiled_par = compile_query_parallel(schema._schema, query)
    start = time.perf_counter()
    for _ in range(5):
        result = await compiled_par(root)
    parallel_time = time.perf_counter() - start

    print("\n" + "=" * 60)
    print("⚡ PARALLEL ASYNC EXECUTION BENCHMARK")
    print("=" * 60)
    print(f"Standard GraphQL:  {standard_time * 1000:.2f}ms")
    print(
        f"Sequential JIT:    {sequential_time * 1000:.2f}ms ({standard_time / sequential_time:.2f}x faster)"
    )
    print(
        f"Parallel JIT:      {parallel_time * 1000:.2f}ms ({standard_time / parallel_time:.2f}x faster)"
    )
    print(f"\nParallel vs Sequential: {sequential_time / parallel_time:.2f}x speedup")

    return standard_time, sequential_time, parallel_time


if __name__ == "__main__":

    async def run_tests():
        class MockSnapshot:
            def __init__(self):
                self.snapshot_dir = None

            def assert_match(self, content, filename):
                print(f"\nGenerated parallel code for {filename}:")
                print("=" * 60)
                # Show first 1000 chars of generated code
                print(content[:1000] + "..." if len(content) > 1000 else content)
                print("=" * 60)

        snapshot = MockSnapshot()

        print("Testing parallel async execution...")

        await test_parallel_execution_simple()
        await test_parallel_execution_nested()
        await test_parallel_execution_mixed()
        await test_parallel_execution_snapshot(snapshot)

        # Run benchmark
        await benchmark_parallel_performance()

        print("\n✅ All parallel async tests passed!")

    asyncio.run(run_tests())
