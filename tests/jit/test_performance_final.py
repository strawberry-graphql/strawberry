"""
Final performance benchmark showing JIT compiler improvements.
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

    @strawberry.field
    def bio(self) -> str:
        return f"Author {self.name}"

    @strawberry.field
    def posts_count(self) -> int:
        return 10


@strawberry.type
class Post:
    id: str
    title: str
    content: str

    def __init__(self, id: str, title: str, content: str):
        self.id = id
        self.title = title
        self.content = content
        self._author = Author(id="a1", name="Alice", email="alice@example.com")

    @strawberry.field
    def author(self) -> Author:
        return self._author

    @strawberry.field
    def word_count(self) -> int:
        return len(self.content.split())

    @strawberry.field
    def is_published(self) -> bool:
        return True


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

    @strawberry.field
    async def async_posts(self, limit: int = 10) -> list[Post]:
        await asyncio.sleep(0.001)  # Simulate DB call
        return [
            Post(
                id=f"p{i}",
                title=f"Post {i}",
                content=f"This is the content for post {i} with some words",
            )
            for i in range(limit)
        ]


def benchmark_sync_queries():
    """Benchmark synchronous queries."""
    schema = strawberry.Schema(Query)

    queries = [
        # Simple query
        (
            "Simple",
            """
        query {
            posts(limit: 50) {
                id
                title
            }
        }
        """,
        ),
        # Nested query
        (
            "Nested",
            """
        query {
            posts(limit: 20) {
                id
                title
                content
                wordCount
                isPublished
                author {
                    name
                    email
                    bio
                    postsCount
                }
            }
        }
        """,
        ),
        # Complex query with multiple field selections
        (
            "Complex",
            """
        query {
            first: posts(limit: 10) {
                id
                title
                author {
                    name
                }
            }
            second: posts(limit: 5) {
                id
                content
                wordCount
                author {
                    email
                    bio
                }
            }
            third: posts(limit: 15) {
                title
                isPublished
            }
        }
        """,
        ),
    ]

    for _name, query in queries:
        root = Query()

        # Warmup
        for _ in range(10):
            execute_sync(schema._schema, parse(query), root_value=root)

        # Standard GraphQL
        start = time.perf_counter()
        for _ in range(100):
            execute_sync(schema._schema, parse(query), root_value=root)
        standard_time = time.perf_counter() - start

        # JIT Compiled
        compiled_fn = compile_query(schema, query)
        start = time.perf_counter()
        for _ in range(100):
            compiled_fn(root)
        jit_time = time.perf_counter() - start

        standard_time / jit_time


async def benchmark_async_queries():
    """Benchmark asynchronous queries."""
    schema = strawberry.Schema(Query)

    queries = [
        # Simple async query
        (
            "Simple Async",
            """
        query {
            asyncPosts(limit: 50) {
                id
                title
            }
        }
        """,
        ),
        # Nested async query
        (
            "Nested Async",
            """
        query {
            asyncPosts(limit: 20) {
                id
                title
                content
                wordCount
                author {
                    name
                    bio
                }
            }
        }
        """,
        ),
    ]

    for _name, query in queries:
        root = Query()

        # Warmup
        for _ in range(10):
            await execute(schema._schema, parse(query), root_value=root)

        # Standard GraphQL
        start = time.perf_counter()
        for _ in range(100):
            await execute(schema._schema, parse(query), root_value=root)
        standard_time = time.perf_counter() - start

        # JIT Compiled
        compiled_fn = compile_query(schema, query)
        start = time.perf_counter()
        for _ in range(100):
            await compiled_fn(root)
        jit_time = time.perf_counter() - start

        standard_time / jit_time


def main():
    # Run sync benchmarks
    benchmark_sync_queries()

    # Run async benchmarks
    asyncio.run(benchmark_async_queries())


if __name__ == "__main__":
    main()
