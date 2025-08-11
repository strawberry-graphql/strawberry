"""
Test JIT compilation with async resolvers.
"""

import asyncio
from pathlib import Path
from typing import List

import pytest
from graphql import execute, parse
from pytest_snapshot.plugin import Snapshot

import strawberry
from strawberry.jit_compiler import GraphQLJITCompiler, compile_query

HERE = Path(__file__).parent


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
async def test_async_simple_field(snapshot: Snapshot):
    """Test JIT compilation with a simple async field."""
    schema = strawberry.Schema(Query)

    query = """
    query HelloWorld {
        hello(name: "GraphQL")
    }
    """

    # Compile the query
    compiler = GraphQLJITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_async"
    snapshot.assert_match(generated_code, "async_simple_field.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    # The compiled function should be async
    assert asyncio.iscoroutinefunction(compiled_fn)

    result = await compiled_fn(root)
    assert result["hello"] == "Hello GraphQL"

    # Compare with standard GraphQL execution
    standard_result = await execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


@pytest.mark.asyncio
async def test_async_nested_fields(snapshot: Snapshot):
    """Test JIT compilation with nested async fields."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts {
        posts(limit: 2) {
            id
            title
            author {
                name
                bio
            }
            viewCount
        }
    }
    """

    # Compile the query
    compiler = GraphQLJITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_async"
    snapshot.assert_match(generated_code, "async_nested_fields.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    result = await compiled_fn(root)

    # Verify results
    assert len(result["posts"]) == 2
    assert result["posts"][0]["id"] == "p1"
    assert result["posts"][0]["author"]["name"] == "Alice"
    assert result["posts"][0]["author"]["bio"] == "Bio of Alice"
    assert result["posts"][0]["viewCount"] == 100

    # Compare with standard GraphQL execution
    standard_result = await execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


@pytest.mark.asyncio
async def test_mixed_sync_async_fields(snapshot: Snapshot):
    """Test JIT compilation with mixed sync and async fields."""
    schema = strawberry.Schema(Query)

    query = """
    query MixedQuery {
        syncPosts {
            id
            title
            syncAuthor {
                name
            }
        }
        posts {
            id
            author {
                name
            }
        }
    }
    """

    # Compile the query
    compiler = GraphQLJITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_async"
    snapshot.assert_match(generated_code, "mixed_sync_async.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    # Should be async because posts field is async
    assert asyncio.iscoroutinefunction(compiled_fn)

    result = await compiled_fn(root)

    # Verify both sync and async fields work
    assert len(result["syncPosts"]) == 1
    assert result["syncPosts"][0]["syncAuthor"]["name"] == "Alice"
    assert len(result["posts"]) == 2
    assert result["posts"][0]["author"]["name"] == "Alice"

    # Compare with standard GraphQL execution
    standard_result = await execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


@pytest.mark.asyncio
async def test_async_with_list_fields(snapshot: Snapshot):
    """Test JIT compilation with async fields returning lists."""
    schema = strawberry.Schema(Query)

    query = """
    query GetComments {
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

    # Compile the query
    compiler = GraphQLJITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_async"
    snapshot.assert_match(generated_code, "async_list_fields.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    result = await compiled_fn(root)

    # Verify results
    assert len(result["posts"]) == 2
    assert len(result["posts"][0]["comments"]) == 2
    assert result["posts"][0]["comments"][0]["text"] == "Great post!"
    assert result["posts"][0]["comments"][0]["likes"] == 42

    # Compare with standard GraphQL execution
    standard_result = await execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_sync_only_query():
    """Test that sync-only queries generate sync functions."""

    @strawberry.type
    class SimpleQuery:
        @strawberry.field
        def name(self) -> str:
            return "Sync Field"

        @strawberry.field
        def count(self) -> int:
            return 42

    schema = strawberry.Schema(SimpleQuery)

    query = """
    query SyncOnly {
        name
        count
    }
    """

    # Compile the query
    compiled_fn = compile_query(schema._schema, query)
    root = SimpleQuery()

    # Should NOT be async
    assert not asyncio.iscoroutinefunction(compiled_fn)

    # Can call synchronously
    result = compiled_fn(root)
    assert result["name"] == "Sync Field"
    assert result["count"] == 42


@pytest.mark.asyncio
async def test_async_with_variables(snapshot: Snapshot):
    """Test async JIT compilation with variables."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts($limit: Int!) {
        posts(limit: $limit) {
            id
            title
            viewCount
        }
    }
    """

    # Compile the query
    compiler = GraphQLJITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_async"
    snapshot.assert_match(generated_code, "async_with_variables.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    result = await compiled_fn(root, variables={"limit": 1})

    # Verify results
    assert len(result["posts"]) == 1
    assert result["posts"][0]["viewCount"] == 100

    # Compare with standard GraphQL execution
    standard_result = await execute(
        schema._schema, parse(query), root_value=root, variable_values={"limit": 1}
    )
    assert result == standard_result.data


@pytest.mark.asyncio
async def test_async_with_fragments(snapshot: Snapshot):
    """Test async JIT compilation with fragments."""
    schema = strawberry.Schema(Query)

    query = """
    fragment PostFields on Post {
        id
        title
        viewCount
    }

    query GetPosts {
        posts {
            ...PostFields
            author {
                name
                bio
            }
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    result = await compiled_fn(root)

    # Verify results
    assert len(result["posts"]) == 2
    assert result["posts"][0]["viewCount"] == 100
    assert result["posts"][0]["author"]["bio"] == "Bio of Alice"

    # Compare with standard GraphQL execution
    standard_result = await execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


if __name__ == "__main__":
    # Run async tests
    async def run_tests():

        class MockSnapshot:
            def __init__(self):
                self.snapshot_dir = None

            def assert_match(self, content, filename):
                print(
                    f"Would save snapshot to: {self.snapshot_dir / filename if self.snapshot_dir else filename}"
                )

        snapshot = MockSnapshot()

        await test_async_simple_field(snapshot)
        await test_async_nested_fields(snapshot)
        await test_mixed_sync_async_fields(snapshot)
        await test_async_with_list_fields(snapshot)
        await test_async_with_variables(snapshot)
        await test_async_with_fragments(snapshot)

        test_sync_only_query()

        print("\n✅ All async JIT tests passed!")

    asyncio.run(run_tests())
