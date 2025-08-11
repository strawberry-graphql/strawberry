"""
Test query caching in JIT compiler.
"""

import asyncio
import time
from typing import List

import pytest

import strawberry
from strawberry.jit_compiler_cached import (
    CachedJITCompiler,
    QueryCache,
    clear_global_cache,
    compile_query,
    compile_query_global,
    get_global_cache_stats,
)


@strawberry.type
class Author:
    id: str
    name: str

    @strawberry.field
    def posts_count(self) -> int:
        return 5


@strawberry.type
class Post:
    id: str
    title: str
    content: str

    @strawberry.field
    def author(self) -> Author:
        return Author(id="a1", name="Alice")

    @strawberry.field
    def word_count(self) -> int:
        # Simulate some computation
        time.sleep(0.001)  # 1ms
        return len(self.content.split())


@strawberry.type
class Query:
    @strawberry.field
    def posts(self, limit: int = 10) -> List[Post]:
        return [
            Post(id=f"p{i}", title=f"Post {i}", content=f"Content for post {i}")
            for i in range(limit)
        ]

    @strawberry.field
    async def async_posts(self, limit: int = 10) -> List[Post]:
        await asyncio.sleep(0.001)
        return [
            Post(
                id=f"p{i}",
                title=f"Async Post {i}",
                content=f"Async content for post {i}",
            )
            for i in range(limit)
        ]


def test_cache_basic():
    """Test basic cache functionality."""
    cache = QueryCache(max_size=10)

    # Test cache miss
    assert cache.get("schema1", "query { test }") is None
    assert cache.stats.misses == 1
    assert cache.stats.hits == 0

    # Store a value
    def dummy_fn():
        return "result"

    cache.put("schema1", "query { test }", dummy_fn)
    assert cache.size() == 1

    # Test cache hit
    cached_fn = cache.get("schema1", "query { test }")
    assert cached_fn is dummy_fn
    assert cache.stats.hits == 1
    assert cache.stats.misses == 1

    # Test hit rate
    assert cache.stats.hit_rate == 0.5


def test_cache_normalization():
    """Test that query normalization improves cache hits."""
    cache = QueryCache()

    def dummy_fn():
        return "result"

    # Different formatting of the same query
    query1 = "query { posts { id title } }"
    query2 = """
    query {
        posts {
            id
            title
        }
    }
    """

    # Both should generate the same cache key after normalization
    cache.put("schema1", query1, dummy_fn)

    # This should be a cache hit despite different formatting
    cached_fn = cache.get("schema1", query2)
    assert cached_fn is dummy_fn


def test_cache_lru_eviction():
    """Test LRU eviction policy."""
    cache = QueryCache(max_size=3)

    # Fill the cache
    for i in range(3):
        cache.put("schema1", f"query{i}", lambda i=i: f"result{i}")

    assert cache.size() == 3
    assert cache.stats.evictions == 0

    # Access query0 and query1 to make them more recently used
    cache.get("schema1", "query0")
    cache.get("schema1", "query1")

    # Add a new query, should evict query2 (least recently used)
    cache.put("schema1", "query3", lambda: "result3")

    assert cache.size() == 3
    assert cache.stats.evictions == 1

    # query2 should be evicted
    assert cache.get("schema1", "query2") is None
    # Others should still be there
    assert cache.get("schema1", "query0") is not None
    assert cache.get("schema1", "query1") is not None
    assert cache.get("schema1", "query3") is not None


def test_cache_ttl():
    """Test cache TTL expiration."""
    cache = QueryCache(ttl=0.1)  # 100ms TTL

    def dummy_fn():
        return "result"

    cache.put("schema1", "query { test }", dummy_fn)

    # Should be in cache immediately
    assert cache.get("schema1", "query { test }") is not None

    # Wait for expiration
    time.sleep(0.15)

    # Should be expired
    assert cache.get("schema1", "query { test }") is None


def test_cached_jit_compiler():
    """Test the cached JIT compiler."""
    schema = strawberry.Schema(Query)
    compiler = CachedJITCompiler(schema._schema, cache_size=10)

    query = """
    query GetPosts {
        posts(limit: 5) {
            id
            title
            author {
                name
            }
        }
    }
    """

    # First compilation - cache miss
    start = time.perf_counter()
    compiled_fn1 = compiler.compile_query(query)
    first_time = time.perf_counter() - start

    assert compiler.cache.stats.misses == 1
    assert compiler.cache.stats.hits == 0

    # Second compilation - cache hit
    start = time.perf_counter()
    compiled_fn2 = compiler.compile_query(query)
    second_time = time.perf_counter() - start

    assert compiler.cache.stats.misses == 1
    assert compiler.cache.stats.hits == 1

    # Should be the same function
    assert compiled_fn1 is compiled_fn2

    # Cache hit should be much faster
    print(f"\n  First compilation:  {first_time * 1000:.3f}ms")
    print(f"  Cache hit:          {second_time * 1000:.3f}ms")
    print(f"  Speedup:            {first_time / second_time:.1f}x")
    assert second_time < first_time * 0.5  # At least 2x faster

    # Test execution
    root = Query()
    result = compiled_fn1(root)
    assert len(result["posts"]) == 5
    assert result["posts"][0]["author"]["name"] == "Alice"


@pytest.mark.asyncio
async def test_cached_async_queries():
    """Test caching with async queries."""
    schema = strawberry.Schema(Query)
    compiler = CachedJITCompiler(schema._schema, enable_parallel=True)

    query = """
    query GetAsyncPosts {
        asyncPosts(limit: 3) {
            id
            title
        }
    }
    """

    # Compile twice
    compiled_fn1 = compiler.compile_query(query)
    compiled_fn2 = compiler.compile_query(query)

    # Should be cached
    assert compiled_fn1 is compiled_fn2
    assert compiler.cache.stats.hits == 1

    # Execute
    root = Query()
    result = await compiled_fn1(root)
    assert len(result["asyncPosts"]) == 3


def test_global_cache():
    """Test the global cache functionality."""
    # Clear any existing global cache
    clear_global_cache()

    schema1 = strawberry.Schema(Query)
    schema2 = strawberry.Schema(Query)  # Different schema instance

    query = "query { posts { id } }"

    # Compile with global cache
    compiled_fn1 = compile_query_global(schema1._schema, query)

    # Check stats
    stats = get_global_cache_stats()
    assert stats.misses == 1
    assert stats.hits == 0

    # Compile same query again
    compiled_fn2 = compile_query_global(schema1._schema, query)

    # Should be cached
    assert compiled_fn1 is compiled_fn2
    stats = get_global_cache_stats()
    assert stats.hits == 1

    # Different schema should have different cache entry
    compiled_fn3 = compile_query_global(schema2._schema, query)
    assert compiled_fn3 is not compiled_fn1  # Different schema, different function

    stats = get_global_cache_stats()
    assert stats.misses == 2  # One more miss for schema2


def test_cache_performance_benefit():
    """Measure the performance benefit of caching."""
    schema = strawberry.Schema(Query)

    queries = [
        "query { posts { id title } }",
        "query { posts { id title content } }",
        "query { posts { id author { name } } }",
    ]

    # Without caching - compile each time
    from strawberry.jit import compile_query

    start = time.perf_counter()
    for _ in range(10):
        for query in queries:
            compiled_fn = compile_query(schema._schema, query)
    no_cache_time = time.perf_counter() - start

    # With caching - compile once, reuse
    compiler = CachedJITCompiler(schema._schema, cache_size=100)
    start = time.perf_counter()
    for _ in range(10):
        for query in queries:
            compiled_fn = compiler.compile_query(query)
    cache_time = time.perf_counter() - start

    print("\n📊 Cache Performance:")
    print(f"  Without cache: {no_cache_time * 1000:.2f}ms")
    print(f"  With cache:    {cache_time * 1000:.2f}ms")
    print(f"  Speedup:       {no_cache_time / cache_time:.2f}x")

    # Caching should provide significant speedup
    assert cache_time < no_cache_time  # Should be faster


def test_cache_with_variables():
    """Test that queries with different variables use the same cached function."""
    schema = strawberry.Schema(Query)
    compiler = CachedJITCompiler(schema._schema)

    query = """
    query GetPosts($limit: Int!) {
        posts(limit: $limit) {
            id
            title
        }
    }
    """

    # Compile with different variable values
    # Variables don't affect compilation, only execution
    compiled_fn1 = compiler.compile_query(query)
    compiled_fn2 = compiler.compile_query(query)

    # Should be the same cached function
    assert compiled_fn1 is compiled_fn2
    assert compiler.cache.stats.hits == 1

    # Test execution with different variables
    root = Query()
    result1 = compiled_fn1(root, variables={"limit": 3})
    result2 = compiled_fn1(root, variables={"limit": 5})

    assert len(result1["posts"]) == 3
    assert len(result2["posts"]) == 5


def test_convenience_functions():
    """Test the convenience functions for caching."""
    schema = strawberry.Schema(Query)

    query = "query { posts { id } }"

    # Test compile_query
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)
    assert len(result["posts"]) == 10

    # Test with parallel execution
    compiled_fn_parallel = compile_query(schema._schema, query, enable_parallel=True)
    result = compiled_fn_parallel(root)
    assert len(result["posts"]) == 10


def benchmark_cache_impact():
    """Benchmark the impact of caching on a realistic workload."""
    schema = strawberry.Schema(Query)

    # Simulate a realistic query mix
    queries = [
        "query { posts(limit: 10) { id title } }",
        "query { posts(limit: 20) { id title content wordCount } }",
        "query { posts { id author { name postsCount } } }",
        "query { posts(limit: 5) { id title author { id name } } }",
        "query { posts { id title content } }",
    ]

    # Simulate query distribution (some queries more frequent)
    query_distribution = [0, 0, 1, 0, 2, 1, 0, 3, 0, 4] * 10  # 100 queries

    print("\n" + "=" * 60)
    print("📊 CACHE IMPACT BENCHMARK")
    print("=" * 60)

    # Without cache
    from strawberry.jit import compile_query

    start = time.perf_counter()
    root = Query()
    for query_idx in query_distribution:
        query = queries[query_idx]
        compiled_fn = compile_query(schema._schema, query)
        result = compiled_fn(root)
    no_cache_time = time.perf_counter() - start

    # With cache
    compiler = CachedJITCompiler(schema._schema, cache_size=100)
    start = time.perf_counter()
    for query_idx in query_distribution:
        query = queries[query_idx]
        compiled_fn = compiler.compile_query(query)
        result = compiled_fn(root)
    cache_time = time.perf_counter() - start

    stats = compiler.get_cache_stats()

    print(f"\nWorkload: {len(query_distribution)} queries, {len(queries)} unique")
    print(f"\nWithout cache: {no_cache_time * 1000:.2f}ms")
    print(f"With cache:    {cache_time * 1000:.2f}ms")
    print(f"Speedup:       {no_cache_time / cache_time:.2f}x")
    print(f"\nCache stats: {stats}")
    print(f"Memory used:   {compiler.cache.size()} entries")

    # Should show significant improvement
    assert cache_time < no_cache_time
    assert stats.hit_rate > 0.8  # Most queries should hit cache


if __name__ == "__main__":
    # Run tests
    print("Testing query caching...")

    test_cache_basic()
    test_cache_normalization()
    test_cache_lru_eviction()
    test_cache_ttl()
    test_cached_jit_compiler()
    test_global_cache()
    test_cache_performance_benefit()
    test_cache_with_variables()
    test_convenience_functions()

    # Run async tests
    asyncio.run(test_cached_async_queries())

    # Run benchmark
    benchmark_cache_impact()

    print("\n✅ All caching tests passed!")
