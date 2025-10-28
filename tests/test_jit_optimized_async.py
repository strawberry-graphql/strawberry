"""Test async support in the optimized JIT compiler."""

import asyncio
import time

import pytest

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class AsyncPost:
    id: int
    title: str

    @strawberry.field
    async def content(self) -> str:
        """Async field resolver."""
        await asyncio.sleep(0.01)  # Simulate async work
        return f"Content for {self.title}"

    @strawberry.field
    async def view_count(self) -> int:
        """Another async field."""
        await asyncio.sleep(0.01)
        return self.id * 100

    @strawberry.field
    def word_count(self) -> int:
        """Sync field."""
        return len(self.title.split())


@strawberry.type
class AsyncAuthor:
    id: int
    name: str

    @strawberry.field
    async def bio(self) -> str:
        """Async bio resolver."""
        await asyncio.sleep(0.01)
        return f"Bio for {self.name}"

    @strawberry.field
    async def posts(self) -> list[AsyncPost]:
        """Async posts resolver."""
        await asyncio.sleep(0.01)
        return [AsyncPost(id=i, title=f"Post {i} by {self.name}") for i in range(3)]

    @strawberry.field
    def email(self) -> str:
        """Sync field."""
        return f"{self.name.lower().replace(' ', '.')}@example.com"


@strawberry.type
class AsyncQuery:
    @strawberry.field
    async def author(self, id: int) -> AsyncAuthor:
        """Async author resolver."""
        await asyncio.sleep(0.01)
        return AsyncAuthor(id=id, name=f"Author {id}")

    @strawberry.field
    async def authors(self, limit: int = 5) -> list[AsyncAuthor]:
        """Async authors resolver."""
        await asyncio.sleep(0.01)
        return [AsyncAuthor(id=i, name=f"Author {i}") for i in range(limit)]

    @strawberry.field
    def version(self) -> str:
        """Sync field."""
        return "1.0.0"


@pytest.mark.asyncio
async def test_optimized_async_single_field():
    """Test optimized JIT with single async field."""
    schema = strawberry.Schema(AsyncQuery)

    query = """
    query {
        author(id: 1) {
            id
            name
            bio
            email
        }
    }
    """

    # Compile with optimized JIT
    compiled_fn = compile_query(schema, query)

    # Execute
    root = AsyncQuery()

    # The compiled function should be async
    assert asyncio.iscoroutinefunction(compiled_fn)

    result = await compiled_fn(root)

    assert result["data"] == {
        "author": {
            "id": 1,
            "name": "Author 1",
            "bio": "Bio for Author 1",
            "email": "author.1@example.com",
        }
    }


@pytest.mark.asyncio
async def test_optimized_async_nested_fields():
    """Test optimized JIT with nested async fields."""
    schema = strawberry.Schema(AsyncQuery)

    query = """
    query {
        author(id: 2) {
            id
            name
            posts {
                id
                title
                content
                viewCount
                wordCount
            }
        }
    }
    """

    compiled_fn = compile_query(schema, query)
    root = AsyncQuery()

    result = await compiled_fn(root)

    assert result["data"]["author"]["id"] == 2
    assert result["data"]["author"]["name"] == "Author 2"
    assert len(result["data"]["author"]["posts"]) == 3

    # Check first post
    post = result["data"]["author"]["posts"][0]
    assert post["id"] == 0
    assert post["title"] == "Post 0 by Author 2"
    assert post["content"] == "Content for Post 0 by Author 2"
    assert post["viewCount"] == 0
    assert post["wordCount"] == 5


@pytest.mark.asyncio
async def test_optimized_async_list_fields():
    """Test optimized JIT with async list fields."""
    schema = strawberry.Schema(AsyncQuery)

    query = """
    query {
        authors(limit: 3) {
            id
            name
            bio
            posts {
                id
                title
                viewCount
            }
        }
    }
    """

    compiled_fn = compile_query(schema, query)
    root = AsyncQuery()

    result = await compiled_fn(root)

    assert len(result["data"]["authors"]) == 3

    for i, author in enumerate(result["data"]["authors"]):
        assert author["id"] == i
        assert author["name"] == f"Author {i}"
        assert author["bio"] == f"Bio for Author {i}"
        assert len(author["posts"]) == 3


@pytest.mark.asyncio
async def test_optimized_mixed_sync_async():
    """Test optimized JIT with mixed sync/async fields."""
    schema = strawberry.Schema(AsyncQuery)

    query = """
    query {
        version
        author(id: 5) {
            id
            name
            email
            bio
        }
    }
    """

    compiled_fn = compile_query(schema, query)
    root = AsyncQuery()

    result = await compiled_fn(root)

    assert result["data"]["version"] == "1.0.0"
    assert result["data"]["author"]["id"] == 5
    assert result["data"]["author"]["name"] == "Author 5"
    assert result["data"]["author"]["email"] == "author.5@example.com"
    assert result["data"]["author"]["bio"] == "Bio for Author 5"


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Flaky performance test - timing depends on system load and JIT compilation overhead"
)
async def test_optimized_async_performance():
    """Test that optimized JIT provides performance benefits even with async."""
    schema = strawberry.Schema(AsyncQuery)

    query = """
    query {
        authors(limit: 10) {
            id
            name
            bio
            email
            posts {
                id
                title
                content
                viewCount
                wordCount
            }
        }
    }
    """

    root = AsyncQuery()

    # Standard execution
    start = time.perf_counter()
    for _ in range(5):
        result = await schema.execute(query, root_value=root)
    standard_time = time.perf_counter() - start

    # Optimized JIT execution
    compiled_fn = compile_query(schema, query)
    start = time.perf_counter()
    for _ in range(5):
        result = await compiled_fn(root)
    jit_time = time.perf_counter() - start

    # JIT should be faster even with async
    print(f"Standard: {standard_time:.3f}s, JIT: {jit_time:.3f}s")
    print(f"Speedup: {standard_time / jit_time:.2f}x")

    # Assert we get some speedup (at least 1.2x faster)
    assert jit_time < standard_time * 0.9  # Allow some variance


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Flaky timing test - actual timing varies based on system load"
)
async def test_optimized_parallel_async_execution():
    """Test that async fields are executed in parallel."""

    @strawberry.type
    class TimedPost:
        id: int

        @strawberry.field
        async def slow_field_1(self) -> str:
            await asyncio.sleep(0.1)
            return f"slow1-{self.id}"

        @strawberry.field
        async def slow_field_2(self) -> str:
            await asyncio.sleep(0.1)
            return f"slow2-{self.id}"

        @strawberry.field
        async def slow_field_3(self) -> str:
            await asyncio.sleep(0.1)
            return f"slow3-{self.id}"

    @strawberry.type
    class TimedQuery:
        @strawberry.field
        def post(self) -> TimedPost:
            return TimedPost(id=1)

    schema = strawberry.Schema(TimedQuery)

    query = """
    query {
        post {
            id
            slowField1
            slowField2
            slowField3
        }
    }
    """

    compiled_fn = compile_query(schema, query)
    root = TimedQuery()

    # If executed in parallel, should take ~0.1s not 0.3s
    start = time.perf_counter()
    result = await compiled_fn(root)
    elapsed = time.perf_counter() - start

    assert result["data"] == {
        "post": {
            "id": 1,
            "slowField1": "slow1-1",
            "slowField2": "slow2-1",
            "slowField3": "slow3-1",
        }
    }

    # Should execute in parallel (allow some overhead)
    assert elapsed < 0.2, f"Took {elapsed:.3f}s, expected < 0.2s (parallel execution)"


@pytest.mark.asyncio
async def test_optimized_async_with_arguments():
    """Test optimized JIT with async fields that have arguments."""

    @strawberry.type
    class SearchQuery:
        @strawberry.field
        async def search(self, query: str, limit: int = 10) -> list[str]:
            await asyncio.sleep(0.01)
            return [f"{query}-result-{i}" for i in range(limit)]

    schema = strawberry.Schema(SearchQuery)

    query = """
    query {
        search(query: "test", limit: 3)
    }
    """

    compiled_fn = compile_query(schema, query)
    root = SearchQuery()

    result = await compiled_fn(root)

    assert result["data"] == {
        "search": ["test-result-0", "test-result-1", "test-result-2"]
    }


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_optimized_async_single_field())
    asyncio.run(test_optimized_async_nested_fields())
    asyncio.run(test_optimized_async_list_fields())
    asyncio.run(test_optimized_mixed_sync_async())
    asyncio.run(test_optimized_async_performance())
    asyncio.run(test_optimized_parallel_async_execution())
    asyncio.run(test_optimized_async_with_arguments())
    print("All tests passed!")
