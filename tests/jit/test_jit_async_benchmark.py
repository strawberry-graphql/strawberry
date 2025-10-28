"""
Benchmark async JIT compilation performance vs standard GraphQL execution.
"""

import asyncio
import time

from graphql import execute, parse

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class Author:
    id: str
    name: str
    email: str

    @strawberry.field
    async def posts_count(self) -> int:
        """Simulate async database query."""
        await asyncio.sleep(0.001)  # Simulate 1ms database latency
        return 5

    @strawberry.field
    def sync_posts_count(self) -> int:
        """Sync version for comparison."""
        return 5


@strawberry.type
class Comment:
    id: str
    text: str
    author_id: str

    @strawberry.field
    async def author(self) -> Author:
        """Simulate async author fetch."""
        await asyncio.sleep(0.001)  # Simulate 1ms database latency
        return Author(
            id=self.author_id,
            name=f"Author {self.author_id}",
            email=f"author{self.author_id}@example.com",
        )


@strawberry.type
class Post:
    id: str
    title: str
    content: str
    author_id: str

    @strawberry.field
    async def author(self) -> Author:
        """Simulate async database query for author."""
        await asyncio.sleep(0.001)  # Simulate 1ms database latency
        return Author(
            id=self.author_id,
            name=f"Author {self.author_id}",
            email=f"author{self.author_id}@example.com",
        )

    @strawberry.field
    def sync_author(self) -> Author:
        """Sync version for comparison."""
        return Author(
            id=self.author_id,
            name=f"Author {self.author_id}",
            email=f"author{self.author_id}@example.com",
        )

    @strawberry.field
    async def comments(self, limit: int = 10) -> list[Comment]:
        """Simulate async database query for comments."""
        await asyncio.sleep(0.002)  # Simulate 2ms database latency
        return [
            Comment(id=f"c{i}", text=f"Comment {i}", author_id=f"a{i}")
            for i in range(limit)
        ]

    @strawberry.field
    def sync_comments(self, limit: int = 10) -> list[Comment]:
        """Sync version for comparison."""
        return [
            Comment(id=f"c{i}", text=f"Comment {i}", author_id=f"a{i}")
            for i in range(limit)
        ]

    @strawberry.field
    async def view_count(self) -> int:
        """Simulate async cache/database query."""
        await asyncio.sleep(0.0005)  # Simulate 0.5ms cache latency
        return 100

    @strawberry.field
    def sync_view_count(self) -> int:
        """Sync version."""
        return 100


@strawberry.type
class Query:
    @strawberry.field
    async def posts(self, limit: int = 10) -> list[Post]:
        """Simulate async database query for posts."""
        await asyncio.sleep(0.003)  # Simulate 3ms database latency
        return [
            Post(
                id=f"p{i}",
                title=f"Post {i}",
                content=f"Content {i}",
                author_id=f"a{i % 3}",
            )
            for i in range(limit)
        ]

    @strawberry.field
    def sync_posts(self, limit: int = 10) -> list[Post]:
        """Sync version for comparison."""
        # Simulate some processing time
        time.sleep(0.003)  # Same as async version
        return [
            Post(
                id=f"p{i}",
                title=f"Post {i}",
                content=f"Content {i}",
                author_id=f"a{i % 3}",
            )
            for i in range(limit)
        ]


async def benchmark_sync_query():
    """Benchmark fully synchronous query."""
    schema = strawberry.Schema(Query)

    query = """
    query BenchmarkSync {
        syncPosts(limit: 10) {
            id
            title
            content
            syncAuthor {
                name
                email
            }
            syncViewCount
        }
    }
    """

    root = Query()

    # Standard GraphQL execution (sync query doesn't need await)
    from graphql import execute_sync

    start = time.perf_counter()
    for _ in range(10):
        result = execute_sync(schema._schema, parse(query), root_value=root)
        assert len(result.data["syncPosts"]) == 10
    standard_time = time.perf_counter() - start

    # JIT compiled execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(10):
        result = compiled_fn(root)
        assert len(result["syncPosts"]) == 10
    jit_time = time.perf_counter() - start

    return standard_time, jit_time


async def benchmark_async_query():
    """Benchmark fully asynchronous query."""
    schema = strawberry.Schema(Query)

    query = """
    query BenchmarkAsync {
        posts(limit: 10) {
            id
            title
            content
            author {
                name
                email
                postsCount
            }
            viewCount
        }
    }
    """

    root = Query()

    # Standard GraphQL execution
    start = time.perf_counter()
    for _ in range(10):
        result = await execute(schema._schema, parse(query), root_value=root)
        assert len(result.data["posts"]) == 10
    standard_time = time.perf_counter() - start

    # JIT compiled execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(10):
        result = await compiled_fn(root)
        assert len(result["posts"]) == 10
    jit_time = time.perf_counter() - start

    return standard_time, jit_time


async def benchmark_mixed_query():
    """Benchmark mixed sync/async query."""
    schema = strawberry.Schema(Query)

    query = """
    query BenchmarkMixed {
        posts(limit: 5) {
            id
            title
            content
            author {
                name
                email
            }
            syncViewCount
        }
        syncPosts(limit: 5) {
            id
            title
            syncAuthor {
                name
            }
        }
    }
    """

    root = Query()

    # Standard GraphQL execution
    start = time.perf_counter()
    for _ in range(10):
        result = await execute(schema._schema, parse(query), root_value=root)
        assert len(result.data["posts"]) == 5
        assert len(result.data["syncPosts"]) == 5
    standard_time = time.perf_counter() - start

    # JIT compiled execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(10):
        result = await compiled_fn(root)
        assert len(result["posts"]) == 5
        assert len(result["syncPosts"]) == 5
    jit_time = time.perf_counter() - start

    return standard_time, jit_time


async def benchmark_complex_async_query():
    """Benchmark complex nested async query."""
    schema = strawberry.Schema(Query)

    query = """
    query ComplexAsync {
        posts(limit: 5) {
            id
            title
            author {
                name
                postsCount
            }
            comments(limit: 3) {
                id
                text
                author {
                    name
                    postsCount
                }
            }
            viewCount
        }
    }
    """

    root = Query()

    # Standard GraphQL execution
    start = time.perf_counter()
    for _ in range(5):
        result = await execute(schema._schema, parse(query), root_value=root)
        assert len(result.data["posts"]) == 5
    standard_time = time.perf_counter() - start

    # JIT compiled execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(5):
        result = await compiled_fn(root)
        assert len(result["posts"]) == 5
    jit_time = time.perf_counter() - start

    return standard_time, jit_time


async def benchmark_simple_query():
    """Benchmark simple query without nesting."""
    schema = strawberry.Schema(Query)

    query = """
    query SimpleQuery {
        posts(limit: 100) {
            id
            title
            content
        }
    }
    """

    root = Query()

    # Standard GraphQL execution
    start = time.perf_counter()
    for _ in range(10):
        result = await execute(schema._schema, parse(query), root_value=root)
        assert len(result.data["posts"]) == 100
    standard_time = time.perf_counter() - start

    # JIT compiled execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(10):
        result = await compiled_fn(root)
        assert len(result["posts"]) == 100
    jit_time = time.perf_counter() - start

    return standard_time, jit_time


async def main():
    # Run benchmarks
    results = []

    results.append(("Simple Async", await benchmark_simple_query()))
    results.append(("Sync Query", await benchmark_sync_query()))
    results.append(("Async Query", await benchmark_async_query()))
    results.append(("Mixed Query", await benchmark_mixed_query()))
    results.append(("Complex Async", await benchmark_complex_async_query()))

    # Summary

    total_standard = 0
    total_jit = 0

    for _name, (standard, jit) in results:
        standard / jit
        total_standard += standard
        total_jit += jit

    total_standard / total_jit

    # Calculate overhead percentages
    for _name, (standard, jit) in results:
        ((standard - jit) / standard) * 100


if __name__ == "__main__":
    asyncio.run(main())
