"""
Tests for the GraphQL JIT compiler using Strawberry schemas.
"""

from pathlib import Path
from typing import List

from graphql import execute, parse
from pytest_snapshot.plugin import Snapshot

import strawberry
from strawberry.jit_compiler import GraphQLJITCompiler, compile_query

HERE = Path(__file__).parent


@strawberry.type
class Author:
    id: str
    name: str
    email: str


@strawberry.type
class Post:
    id: str
    title: str
    content: str
    author: Author


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> List[Post]:
        return [
            Post(
                id="1",
                title="First Post",
                content="Hello World",
                author=Author(id="a1", name="Alice", email="alice@example.com"),
            ),
            Post(
                id="2",
                title="Second Post",
                content="GraphQL is great",
                author=Author(id="a2", name="Bob", email="bob@example.com"),
            ),
        ]


def test_simple_query(snapshot: Snapshot):
    """Test JIT compilation of a simple query."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        posts {
            id
            title
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
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_compiler"
    snapshot.assert_match(generated_code, "simple_query.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify result matches expected
    expected_result = {
        "posts": [
            {"id": "1", "title": "First Post"},
            {"id": "2", "title": "Second Post"},
        ]
    }
    assert result == expected_result

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_nested_query(snapshot: Snapshot):
    """Test JIT compilation with nested fields."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        posts {
            title
            author {
                name
                email
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
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_compiler"
    snapshot.assert_match(generated_code, "nested_query.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify result matches expected
    expected_result = {
        "posts": [
            {
                "title": "First Post",
                "author": {"name": "Alice", "email": "alice@example.com"},
            },
            {
                "title": "Second Post",
                "author": {"name": "Bob", "email": "bob@example.com"},
            },
        ]
    }
    assert result == expected_result

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_query_with_aliases(snapshot: Snapshot):
    """Test JIT compilation with field aliases."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        allPosts: posts {
            postId: id
            headline: title
            writer: author {
                fullName: name
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
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_compiler"
    snapshot.assert_match(generated_code, "query_with_aliases.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify result matches expected
    expected_result = {
        "allPosts": [
            {
                "postId": "1",
                "headline": "First Post",
                "writer": {"fullName": "Alice"},
            },
            {
                "postId": "2",
                "headline": "Second Post",
                "writer": {"fullName": "Bob"},
            },
        ]
    }
    assert result == expected_result

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_query_with_typename(snapshot: Snapshot):
    """Test JIT compilation with __typename introspection."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        __typename
        posts {
            __typename
            id
            title
            author {
                __typename
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
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_compiler"
    snapshot.assert_match(generated_code, "query_with_typename.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify result matches expected
    expected_result = {
        "__typename": "Query",
        "posts": [
            {
                "__typename": "Post",
                "id": "1",
                "title": "First Post",
                "author": {"__typename": "Author", "name": "Alice"},
            },
            {
                "__typename": "Post",
                "id": "2",
                "title": "Second Post",
                "author": {"__typename": "Author", "name": "Bob"},
            },
        ],
    }
    assert result == expected_result

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data