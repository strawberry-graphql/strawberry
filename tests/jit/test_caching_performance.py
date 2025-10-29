"""
Comprehensive performance test showing the impact of query caching.
Demonstrates how to implement a simple cache for compiled queries.
"""

import asyncio
import time

import strawberry
from strawberry.jit import compile_query


# Simple cache implementation for demonstration
class SimpleQueryCache:
    """Basic query cache for JIT-compiled queries."""

    def __init__(self, schema, cache_size=100):
        self.schema = schema
        self.cache = {}
        self.cache_size = cache_size
        self.access_order = []

    def compile_query(self, query: str):
        """Compile query with caching."""
        if query in self.cache:
            # Move to end (LRU)
            if query in self.access_order:
                self.access_order.remove(query)
            self.access_order.append(query)
            return self.cache[query]

        # Compile new query
        compiled = compile_query(self.schema, query)
        self.cache[query] = compiled
        self.access_order.append(query)

        # Enforce cache size limit
        while len(self.cache) > self.cache_size:
            oldest = self.access_order.pop(0)
            if oldest in self.cache:
                del self.cache[oldest]

        return compiled

    def get_cache_stats(self):
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.cache_size,
            "keys": list(self.cache.keys()),
        }


@strawberry.type
class Author:
    id: str
    name: str
    email: str

    @strawberry.field
    def posts_count(self) -> int:
        return 10

    @strawberry.field
    async def bio(self) -> str:
        await asyncio.sleep(0.001)
        return f"Bio of {self.name}"


@strawberry.type
class Post:
    id: str
    title: str
    content: str

    @strawberry.field
    def author(self) -> Author:
        return Author(id="a1", name="Alice", email="alice@example.com")

    @strawberry.field
    def word_count(self) -> int:
        return len(self.content.split())

    @strawberry.field
    async def view_count(self) -> int:
        await asyncio.sleep(0.001)
        return 100


@strawberry.type
class Query:
    @strawberry.field
    def posts(self, limit: int = 10) -> list[Post]:
        return [
            Post(
                id=f"p{i}",
                title=f"Post {i}",
                content=f"This is the content for post {i} with some words",
            )
            for i in range(limit)
        ]


def benchmark_compilation_overhead():
    """Measure the overhead of query compilation."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts {
        posts(limit: 20) {
            id
            title
            content
            wordCount
            author {
                name
                email
                postsCount
            }
        }
    }
    """

    # Measure compilation time
    compilation_times = []
    for _ in range(10):
        start = time.perf_counter()
        compiled_fn = compile_query(schema, query)
        compilation_times.append(time.perf_counter() - start)

    avg_compilation = sum(compilation_times) / len(compilation_times)

    # Measure execution time
    root = Query()
    execution_times = []
    for _ in range(100):
        start = time.perf_counter()
        compiled_fn(root)
        execution_times.append(time.perf_counter() - start)

    avg_execution = sum(execution_times) / len(execution_times)

    return avg_compilation, avg_execution


def benchmark_cache_effectiveness():
    """Measure cache effectiveness in a realistic scenario."""
    schema = strawberry.Schema(Query)

    # Simulate a realistic API with common queries
    common_queries = [
        # Most frequent query (40% of traffic)
        "query { posts(limit: 10) { id title } }",
        # Second most frequent (30% of traffic)
        "query { posts { id title author { name } } }",
        # Less frequent (20% of traffic)
        "query { posts(limit: 5) { id title content wordCount } }",
        # Rare query (10% of traffic)
        "query { posts { id author { name email postsCount } } }",
    ]

    # Generate realistic query distribution (1000 queries)
    import random

    random.seed(42)
    query_stream = []
    for _ in range(1000):
        r = random.random()
        if r < 0.4:
            query_stream.append(common_queries[0])
        elif r < 0.7:
            query_stream.append(common_queries[1])
        elif r < 0.9:
            query_stream.append(common_queries[2])
        else:
            query_stream.append(common_queries[3])

    root = Query()

    # Without cache
    start = time.perf_counter()
    for query in query_stream:
        compiled_fn = compile_query(schema, query)
        compiled_fn(root)
    no_cache_time = time.perf_counter() - start

    # With cache
    compiler = SimpleQueryCache(schema, cache_size=100)
    start = time.perf_counter()
    for query in query_stream:
        compiled_fn = compiler.compile_query(query)
        compiled_fn(root)
    cache_time = time.perf_counter() - start

    stats = compiler.get_cache_stats()

    return no_cache_time, cache_time, stats


async def benchmark_cached_async_queries():
    """Benchmark caching with async queries."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts {
        posts(limit: 10) {
            id
            title
            viewCount
            author {
                bio
            }
        }
    }
    """

    root = Query()
    iterations = 100

    # Without cache - standard JIT
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        compiled_fn = compile_query(schema, query)
        await compiled_fn(root)
        times.append(time.perf_counter() - start)
    sum(times)

    # With cache
    compiler = SimpleQueryCache(schema)
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        compiled_fn = compiler.compile_query(query)
        await compiled_fn(root)
        times.append(time.perf_counter() - start)
    sum(times)

    compiler.get_cache_stats()


def main():
    # Run benchmarks
    comp_time, exec_time = benchmark_compilation_overhead()
    prod_no_cache, prod_cache, prod_stats = benchmark_cache_effectiveness()

    # Run async benchmark
    asyncio.run(benchmark_cached_async_queries())

    # Summary


if __name__ == "__main__":
    main()
