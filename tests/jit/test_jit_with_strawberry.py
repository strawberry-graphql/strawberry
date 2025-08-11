"""
Tests for the GraphQL JIT compiler with Strawberry schemas.
"""

from pathlib import Path
from typing import List

from graphql import execute, parse
from pytest_snapshot.plugin import Snapshot

import strawberry
from strawberry.jit import JITCompiler, compile_query

HERE = Path(__file__).parent


@strawberry.type
class Author:
    id: str
    name: str
    email: str

    @strawberry.field
    def display_name(self) -> str:
        """Custom resolver using Strawberry field."""
        return f"{self.name} ({self.email})"


@strawberry.type
class Post:
    id: str
    title: str
    content: str
    author: Author

    @strawberry.field
    def word_count(self) -> int:
        """Custom resolver for word count."""
        return len(self.content.split())


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> List[Post]:
        """Resolver that returns sample posts."""
        return [
            Post(
                id="1",
                title="Introduction to GraphQL",
                content="GraphQL is a query language for APIs and a runtime for fulfilling those queries",
                author=Author(id="a1", name="Alice", email="alice@example.com"),
            ),
            Post(
                id="2",
                title="Understanding JIT Compilation",
                content="JIT compilation can significantly improve GraphQL performance by generating optimized code",
                author=Author(id="a2", name="Bob", email="bob@example.com"),
            ),
        ]

    @strawberry.field
    def featured_post(self) -> Post:
        """Returns a single featured post."""
        return Post(
            id="3",
            title="Featured: GraphQL Best Practices",
            content="Learn the best practices for building scalable GraphQL APIs",
            author=Author(id="a1", name="Alice", email="alice@example.com"),
        )


def test_strawberry_simple_query(snapshot: Snapshot):
    """Test JIT compilation with Strawberry schema."""
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
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_with_strawberry"
    snapshot.assert_match(generated_code, "strawberry_simple_query.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify result matches expected
    expected_result = {
        "posts": [
            {"id": "1", "title": "Introduction to GraphQL"},
            {"id": "2", "title": "Understanding JIT Compilation"},
        ]
    }
    assert result == expected_result

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_strawberry_custom_resolvers(snapshot: Snapshot):
    """Test JIT compilation with custom Strawberry resolvers."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        posts {
            id
            title
            wordCount
            author {
                name
                displayName
            }
        }
    }
    """

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_with_strawberry"
    snapshot.assert_match(generated_code, "strawberry_custom_resolvers.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify result matches expected
    expected_result = {
        "posts": [
            {
                "id": "1",
                "title": "Introduction to GraphQL",
                "wordCount": 14,
                "author": {
                    "name": "Alice",
                    "displayName": "Alice (alice@example.com)",
                },
            },
            {
                "id": "2",
                "title": "Understanding JIT Compilation",
                "wordCount": 12,
                "author": {
                    "name": "Bob",
                    "displayName": "Bob (bob@example.com)",
                },
            },
        ]
    }
    assert result == expected_result

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_strawberry_single_field(snapshot: Snapshot):
    """Test JIT compilation with single field that returns an object."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        featuredPost {
            id
            title
            wordCount
            author {
                name
                email
                displayName
            }
        }
    }
    """

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_with_strawberry"
    snapshot.assert_match(generated_code, "strawberry_single_field.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify result matches expected
    expected_result = {
        "featuredPost": {
            "id": "3",
            "title": "Featured: GraphQL Best Practices",
            "wordCount": 9,
            "author": {
                "name": "Alice",
                "email": "alice@example.com",
                "displayName": "Alice (alice@example.com)",
            },
        }
    }
    assert result == expected_result

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data
