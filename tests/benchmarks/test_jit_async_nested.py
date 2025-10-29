"""Benchmark JIT performance with nested async fields.

This reveals the performance regression that occurs with deeply nested
async field resolution - the key missing benchmark case.
"""

import asyncio

import pytest
from pytest_codspeed.plugin import BenchmarkFixture

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class Author:
    name: str
    email: str

    @strawberry.field
    async def posts_count(self) -> int:
        """Async field - simulates DB query."""
        await asyncio.sleep(0.0001)  # Minimal delay
        return 10


@strawberry.type
class Comment:
    id: str
    text: str

    @strawberry.field
    async def author(self) -> Author:
        """Async nested field."""
        await asyncio.sleep(0.0001)
        return Author(name="Commenter", email="commenter@example.com")


@strawberry.type
class Post:
    id: str
    title: str

    @strawberry.field
    async def author(self) -> Author:
        """Async nested field."""
        await asyncio.sleep(0.0001)
        return Author(name="Author", email="author@example.com")

    @strawberry.field
    async def comments(self, limit: int = 5) -> list[Comment]:
        """Async list field."""
        await asyncio.sleep(0.0001)
        return [Comment(id=f"c{i}", text=f"Comment {i}") for i in range(limit)]


@strawberry.type
class Query:
    @strawberry.field
    async def posts(self, limit: int = 10) -> list[Post]:
        """Root async field."""
        await asyncio.sleep(0.0001)
        return [Post(id=f"p{i}", title=f"Post {i}") for i in range(limit)]


NESTED_ASYNC_QUERY = """
query {
    posts(limit: 10) {
        id
        title
        author {
            name
            email
            postsCount
        }
        comments(limit: 5) {
            id
            text
            author {
                name
            }
        }
    }
}
"""


@pytest.mark.benchmark
def test_jit_nested_async(benchmark: BenchmarkFixture):
    """Benchmark JIT with deeply nested async fields.

    This test reveals the performance regression:
    - 10 posts
    - Each post has async author + async comments
    - Each comment has async author
    - 3 levels of async nesting

    Expected: Should be faster or comparable to standard
    Actual: Currently 10-15x SLOWER due to task creation overhead
    """
    schema = strawberry.Schema(query=Query)
    compiled_fn = compile_query(schema, NESTED_ASYNC_QUERY)
    root = Query()

    def run():
        return asyncio.run(compiled_fn(root))

    result = benchmark(run)
    assert result["data"] is not None
    assert len(result["data"]["posts"]) == 10


@pytest.mark.benchmark
def test_standard_nested_async_baseline(benchmark: BenchmarkFixture):
    """Baseline for standard GraphQL with nested async fields."""
    schema = strawberry.Schema(query=Query)
    root = Query()

    def run():
        return asyncio.run(schema.execute(NESTED_ASYNC_QUERY, root_value=root))

    result = benchmark(run)
    assert result.errors is None
    assert result.data is not None
    assert len(result.data["posts"]) == 10
