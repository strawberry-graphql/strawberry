"""
Performance comparison: Standard GraphQL vs JIT compilation.
Shows the performance characteristics of different query types.
"""

import asyncio
import time

from graphql import execute, execute_sync, parse

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class Author:
    id: str
    name: str
    email: str
    posts_count: int = 5


@strawberry.type
class Comment:
    id: str
    text: str
    author: Author


@strawberry.type
class Post:
    id: str
    title: str
    content: str
    author: Author
    comments: list[Comment]
    view_count: int = 100
    published: bool = True


@strawberry.type
class Query:
    @strawberry.field
    def posts(self, limit: int = 10) -> list[Post]:
        """Sync resolver for posts."""
        authors = [
            Author(id=f"a{i}", name=f"Author {i}", email=f"author{i}@example.com")
            for i in range(3)
        ]

        posts = []
        for i in range(limit):
            author = authors[i % 3]
            comments = [
                Comment(
                    id=f"c{i}-{j}",
                    text=f"Comment {j} on post {i}",
                    author=authors[(i + j) % 3],
                )
                for j in range(3)
            ]
            posts.append(
                Post(
                    id=f"p{i}",
                    title=f"Post {i}",
                    content=f"Content for post {i}",
                    author=author,
                    comments=comments,
                )
            )
        return posts

    @strawberry.field
    async def async_posts(self, limit: int = 10) -> list[Post]:
        """Async resolver for posts - simulates database query."""
        await asyncio.sleep(0.001)  # Simulate 1ms database latency
        return self.posts(limit)


def benchmark_sync_simple():
    """Benchmark simple sync query without nesting."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        posts(limit: 100) {
            id
            title
            content
        }
    }
    """

    root = Query()
    parsed_query = parse(query)

    # Warmup
    for _ in range(5):
        execute_sync(schema._schema, parsed_query, root_value=root)

    # Standard GraphQL execution
    iterations = 100
    start = time.perf_counter()
    for _ in range(iterations):
        execute_sync(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - start

    # JIT compiled execution
    compiled_fn = compile_query(schema, query)

    # Warmup
    for _ in range(5):
        compiled_fn(root)

    start = time.perf_counter()
    for _ in range(iterations):
        compiled_fn(root)
    jit_time = time.perf_counter() - start

    return standard_time, jit_time, iterations


def benchmark_sync_nested():
    """Benchmark nested sync query."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        posts(limit: 20) {
            id
            title
            content
            author {
                id
                name
                email
            }
            viewCount
            published
        }
    }
    """

    root = Query()
    parsed_query = parse(query)

    # Warmup
    for _ in range(5):
        execute_sync(schema._schema, parsed_query, root_value=root)

    # Standard GraphQL execution
    iterations = 100
    start = time.perf_counter()
    for _ in range(iterations):
        execute_sync(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - start

    # JIT compiled execution
    compiled_fn = compile_query(schema, query)

    # Warmup
    for _ in range(5):
        compiled_fn(root)

    start = time.perf_counter()
    for _ in range(iterations):
        compiled_fn(root)
    jit_time = time.perf_counter() - start

    return standard_time, jit_time, iterations


def benchmark_sync_complex():
    """Benchmark complex sync query with deep nesting."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        posts(limit: 10) {
            id
            title
            content
            author {
                id
                name
                email
                postsCount
            }
            comments {
                id
                text
                author {
                    id
                    name
                    email
                }
            }
            viewCount
            published
        }
    }
    """

    root = Query()
    parsed_query = parse(query)

    # Warmup
    for _ in range(5):
        execute_sync(schema._schema, parsed_query, root_value=root)

    # Standard GraphQL execution
    iterations = 50
    start = time.perf_counter()
    for _ in range(iterations):
        execute_sync(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - start

    # JIT compiled execution
    compiled_fn = compile_query(schema, query)

    # Warmup
    for _ in range(5):
        compiled_fn(root)

    start = time.perf_counter()
    for _ in range(iterations):
        compiled_fn(root)
    jit_time = time.perf_counter() - start

    return standard_time, jit_time, iterations


async def benchmark_async_simple():
    """Benchmark simple async query."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        asyncPosts(limit: 10) {
            id
            title
            content
        }
    }
    """

    root = Query()
    parsed_query = parse(query)

    # Warmup
    for _ in range(5):
        await execute(schema._schema, parsed_query, root_value=root)

    # Standard GraphQL execution
    iterations = 100
    start = time.perf_counter()
    for _ in range(iterations):
        await execute(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - start

    # JIT compiled execution
    compiled_fn = compile_query(schema, query)

    # Warmup
    for _ in range(5):
        await compiled_fn(root)

    start = time.perf_counter()
    for _ in range(iterations):
        await compiled_fn(root)
    jit_time = time.perf_counter() - start

    return standard_time, jit_time, iterations


def main():
    # Sync benchmarks

    # Simple query
    standard, jit, iterations = benchmark_sync_simple()
    standard / jit

    # Nested query
    standard, jit, iterations = benchmark_sync_nested()
    standard / jit

    # Complex query
    standard, jit, iterations = benchmark_sync_complex()
    standard / jit

    # Async benchmarks

    # Run async benchmark
    async def run_async():
        standard, jit, iterations = await benchmark_async_simple()
        standard / jit

    asyncio.run(run_async())


if __name__ == "__main__":
    main()
