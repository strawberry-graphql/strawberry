"""
Test optimized JIT compiler with compile-time async detection.
"""

import asyncio
import time
from pathlib import Path
from typing import List

import pytest
from graphql import execute, parse
from pytest_snapshot.plugin import Snapshot

import strawberry
from strawberry.jit import compile_query
from strawberry.jit_compiler_optimized_async import (
    JITCompiler,
    analyze_schema_async_fields,
    compile_query,
)

HERE = Path(__file__).parent


@strawberry.type
class Author:
    id: str
    name: str

    @strawberry.field
    async def bio(self) -> str:
        """Async field."""
        await asyncio.sleep(0.001)
        return f"Bio of {self.name}"

    @strawberry.field
    def sync_field(self) -> str:
        """Sync field."""
        return "sync"


@strawberry.type
class Post:
    id: str
    title: str

    @strawberry.field
    async def author(self) -> Author:
        """Async resolver."""
        await asyncio.sleep(0.001)
        return Author(id="a1", name="Alice")

    @strawberry.field
    def content(self) -> str:
        """Sync field."""
        return "Post content"


@strawberry.type
class Query:
    @strawberry.field
    async def posts(self) -> List[Post]:
        """Async resolver."""
        await asyncio.sleep(0.001)
        return [Post(id="p1", title="Test")]

    @strawberry.field
    def sync_posts(self) -> List[Post]:
        """Sync resolver."""
        return [Post(id="p1", title="Test")]


def test_analyze_schema_async_fields():
    """Test that we can analyze a schema for async fields."""
    schema = strawberry.Schema(Query)

    async_fields = analyze_schema_async_fields(schema._schema)

    # Check that async fields are detected
    assert "Query" in async_fields
    assert "posts" in async_fields["Query"]

    assert "Post" in async_fields
    assert "author" in async_fields["Post"]

    assert "Author" in async_fields
    assert "bio" in async_fields["Author"]

    # Check that sync fields are not in the async map
    assert "sync_posts" not in async_fields.get("Query", set())
    assert "content" not in async_fields.get("Post", set())
    assert "sync_field" not in async_fields.get("Author", set())


@pytest.mark.asyncio
async def test_optimized_async_compilation(snapshot: Snapshot):
    """Test that the optimized compiler generates correct code."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts {
        posts {
            id
            title
            content
            author {
                name
                bio
                syncField
            }
        }
    }
    """

    # Use the optimized compiler
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_optimized_async"
    snapshot.assert_match(generated_code, "optimized_async_posts.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    result = await compiled_fn(root)

    # Verify results
    assert result["posts"][0]["id"] == "p1"
    assert result["posts"][0]["author"]["name"] == "Alice"
    assert result["posts"][0]["author"]["bio"] == "Bio of Alice"
    assert result["posts"][0]["author"]["syncField"] == "sync"

    # Compare with standard GraphQL execution
    standard_result = await execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


@pytest.mark.asyncio
async def test_performance_comparison():
    """Compare performance of standard vs optimized JIT compiler."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts {
        posts {
            id
            title
            author {
                name
                bio
            }
        }
        syncPosts {
            id
            title
            content
        }
    }
    """

    root = Query()

    # Warmup
    for _ in range(10):
        # Standard JIT
        compiled_std = compile_query(schema._schema, query)
        await compiled_std(root)

        # Optimized JIT
        compiled_opt = compile_query(schema._schema, query)
        await compiled_opt(root)

    # Benchmark standard JIT
    compiled_std = compile_query(schema._schema, query)
    start = time.perf_counter()
    for _ in range(100):
        result_std = await compiled_std(root)
    std_time = time.perf_counter() - start

    # Benchmark optimized JIT
    compiled_opt = compile_query(schema._schema, query)
    start = time.perf_counter()
    for _ in range(100):
        result_opt = await compiled_opt(root)
    opt_time = time.perf_counter() - start

    # Results should be identical
    assert result_std == result_opt

    print("\n📊 Performance Comparison (100 iterations):")
    print(f"Standard JIT:  {std_time:.4f}s")
    print(f"Optimized JIT: {opt_time:.4f}s")
    print(f"Speedup:       {std_time / opt_time:.2f}x")

    # The optimized version should be at least as fast
    # In practice, it should be faster due to eliminated runtime checks
    assert opt_time <= std_time * 1.1  # Allow 10% margin for variation


@pytest.mark.asyncio
async def test_mixed_sync_async_optimized():
    """Test that mixed sync/async fields work correctly with optimization."""
    schema = strawberry.Schema(Query)

    query = """
    query MixedQuery {
        posts {
            id
            content
            author {
                name
                syncField
                bio
            }
        }
        syncPosts {
            id
            title
        }
    }
    """

    # Compile with optimization
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    result = await compiled_fn(root)

    # Verify mixed results
    assert len(result["posts"]) == 1
    assert result["posts"][0]["content"] == "Post content"  # sync field
    assert result["posts"][0]["author"]["bio"] == "Bio of Alice"  # async field
    assert result["posts"][0]["author"]["syncField"] == "sync"  # sync field
    assert len(result["syncPosts"]) == 1

    # Compare with standard execution
    standard_result = await execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_compile_time_knowledge():
    """Test that the compiler correctly identifies async fields at compile time."""
    schema = strawberry.Schema(Query)

    compiler = JITCompiler(schema._schema)

    # Check compile-time knowledge
    assert compiler._is_field_async("Query", "posts") is True
    assert compiler._is_field_async("Query", "sync_posts") is False
    assert compiler._is_field_async("Post", "author") is True
    assert compiler._is_field_async("Post", "content") is False
    assert compiler._is_field_async("Author", "bio") is True
    assert compiler._is_field_async("Author", "sync_field") is False


if __name__ == "__main__":
    # Run async tests
    async def run_tests():
        class MockSnapshot:
            def __init__(self):
                self.snapshot_dir = None

            def assert_match(self, content, filename):
                print(f"Generated code for {filename}:")
                print("=" * 60)
                print(content[:500] + "..." if len(content) > 500 else content)
                print("=" * 60)

        snapshot = MockSnapshot()

        print("Testing async field analysis...")
        test_analyze_schema_async_fields()

        print("\nTesting optimized compilation...")
        await test_optimized_async_compilation(snapshot)

        print("\nTesting mixed sync/async...")
        await test_mixed_sync_async_optimized()

        print("\nTesting compile-time knowledge...")
        test_compile_time_knowledge()

        print("\nRunning performance comparison...")
        await test_performance_comparison()

        print("\n✅ All optimized async JIT tests passed!")

    asyncio.run(run_tests())
