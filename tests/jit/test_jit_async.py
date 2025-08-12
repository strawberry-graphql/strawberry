"""
Test JIT compilation with async resolvers.
"""

import asyncio
from typing import List

import pytest
from graphql import execute, parse

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class Author:
    id: str
    name: str

    @strawberry.field
    async def bio(self, delay: float = 0) -> str:
        """Async field that simulates fetching bio from database."""
        await asyncio.sleep(delay)
        return f"Bio of {self.name}"


@strawberry.type
class Comment:
    id: str
    text: str

    @strawberry.field
    async def likes(self) -> int:
        """Async field for comment likes."""
        await asyncio.sleep(0.001)
        return 42


@strawberry.type
class Post:
    id: str
    title: str
    content: str

    def __init__(self, id: str, title: str, content: str, author: Author):
        self.id = id
        self.title = title
        self.content = content
        self._author = author
        self._comments = []

    @strawberry.field
    async def author(self) -> Author:
        """Async resolver to fetch author."""
        await asyncio.sleep(0.001)
        return self._author

    @strawberry.field
    def sync_author(self) -> Author:
        """Sync resolver for comparison."""
        return self._author

    @strawberry.field
    async def comments(self) -> List[Comment]:
        """Async resolver to fetch comments."""
        await asyncio.sleep(0.001)
        return [
            Comment(id="c1", text="Great post!"),
            Comment(id="c2", text="Thanks for sharing!"),
        ]

    @strawberry.field
    async def view_count(self) -> int:
        """Async field simulating a database query."""
        await asyncio.sleep(0.001)
        return 100


@strawberry.type
class Query:
    @strawberry.field
    async def posts(self, limit: int = 10) -> List[Post]:
        """Async resolver to fetch posts."""
        await asyncio.sleep(0.001)

        author1 = Author(id="a1", name="Alice")
        author2 = Author(id="a2", name="Bob")

        return [
            Post(
                id="p1",
                title="GraphQL Basics",
                content="Introduction to GraphQL",
                author=author1,
            ),
            Post(
                id="p2",
                title="Advanced GraphQL",
                content="Deep dive into GraphQL",
                author=author2,
            ),
        ][:limit]

    @strawberry.field
    def sync_posts(self) -> List[Post]:
        """Sync resolver for comparison."""
        author1 = Author(id="a1", name="Alice")
        return [
            Post(
                id="p1",
                title="GraphQL Basics",
                content="Introduction to GraphQL",
                author=author1,
            ),
        ]

    @strawberry.field
    async def hello(self, name: str = "world") -> str:
        """Simple async field."""
        await asyncio.sleep(0.001)
        return f"Hello {name}"


@pytest.mark.asyncio
async def test_async_simple_field():
    """Test JIT compilation with a simple async field."""
    schema = strawberry.Schema(Query)

    query = """
    query HelloWorld {
        hello(name: "GraphQL")
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    jit_result = await compiled_fn(root)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=root)

    # Verify results match
    assert jit_result == standard_result.data
    assert jit_result["hello"] == "Hello GraphQL"


@pytest.mark.asyncio
async def test_async_nested_fields():
    """Test JIT compilation with nested async fields."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts {
        posts(limit: 2) {
            id
            title
            author {
                id
                name
                bio
            }
            viewCount
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    jit_result = await compiled_fn(root)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=root)

    # Verify results match
    assert jit_result == standard_result.data
    assert len(jit_result["posts"]) == 2
    assert jit_result["posts"][0]["author"]["bio"] == "Bio of Alice"
    assert jit_result["posts"][0]["viewCount"] == 100


@pytest.mark.asyncio
async def test_mixed_sync_async_fields():
    """Test JIT compilation with mixed sync and async fields."""
    schema = strawberry.Schema(Query)

    query = """
    query MixedQuery {
        posts(limit: 1) {
            id
            title
            syncAuthor {
                id
                name
            }
            author {
                id
                bio
            }
            comments {
                id
                text
                likes
            }
        }
        syncPosts {
            id
            title
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    jit_result = await compiled_fn(root)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=root)

    # Verify results match
    assert jit_result == standard_result.data
    assert jit_result["posts"][0]["syncAuthor"]["id"] == "a1"
    assert jit_result["posts"][0]["author"]["bio"] == "Bio of Alice"
    assert jit_result["posts"][0]["comments"][0]["likes"] == 42


@pytest.mark.asyncio
async def test_async_with_list_fields():
    """Test JIT compilation with async list fields."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPostsWithComments {
        posts {
            id
            comments {
                id
                text
                likes
            }
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    jit_result = await compiled_fn(root)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=root)

    # Verify results match
    assert jit_result == standard_result.data
    assert len(jit_result["posts"]) == 2
    assert len(jit_result["posts"][0]["comments"]) == 2
    assert all(c["likes"] == 42 for p in jit_result["posts"] for c in p["comments"])


def test_sync_only_query():
    """Test that sync-only queries don't create async functions."""
    schema = strawberry.Schema(Query)

    query = """
    query SyncOnly {
        syncPosts {
            id
            title
            syncAuthor {
                id
                name
            }
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    # This should work synchronously
    jit_result = compiled_fn(root)

    # Execute standard way
    standard_result = execute(schema._schema, parse(query), root_value=root)

    # Verify results match
    assert jit_result == standard_result.data
    assert jit_result["syncPosts"][0]["id"] == "p1"


@pytest.mark.asyncio
async def test_async_with_variables():
    """Test async JIT compilation with variables."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts($limit: Int!, $name: String!) {
        posts(limit: $limit) {
            id
            title
        }
        hello(name: $name)
    }
    """

    variables = {"limit": 1, "name": "Test"}

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    jit_result = await compiled_fn(root, variables=variables)

    # Execute standard way
    standard_result = await execute(
        schema._schema, parse(query), root_value=root, variable_values=variables
    )

    # Verify results match
    assert jit_result == standard_result.data
    assert len(jit_result["posts"]) == 1
    assert jit_result["hello"] == "Hello Test"


@pytest.mark.asyncio
async def test_async_with_fragments():
    """Test async JIT compilation with fragments."""
    schema = strawberry.Schema(Query)

    query = """
    fragment AuthorInfo on Author {
        id
        name
        bio
    }

    query GetPostsWithFragments {
        posts(limit: 1) {
            id
            title
            author {
                ...AuthorInfo
            }
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    jit_result = await compiled_fn(root)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=root)

    # Verify results match
    assert jit_result == standard_result.data
    assert jit_result["posts"][0]["author"]["bio"] == "Bio of Alice"


if __name__ == "__main__":
    # Run async tests
    asyncio.run(test_async_simple_field())
    asyncio.run(test_async_nested_fields())
    asyncio.run(test_mixed_sync_async_fields())
    asyncio.run(test_async_with_list_fields())
    test_sync_only_query()
    asyncio.run(test_async_with_variables())
    asyncio.run(test_async_with_fragments())
    print("✅ All async tests passed!")
