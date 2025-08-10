"""
Tests for the GraphQL JIT compiler with Strawberry schemas.
"""

from typing import List

from graphql import execute, parse
from inline_snapshot import snapshot

import strawberry
from strawberry.jit_compiler import compile_query


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


def test_strawberry_simple_query():
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

    # Compile and execute with JIT
    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Query())

    # Check result
    assert result == snapshot(
        {
            "posts": [
                {"id": "1", "title": "Introduction to GraphQL"},
                {"id": "2", "title": "Understanding JIT Compilation"},
            ]
        }
    )

    # Compare with standard execution
    standard_result = execute(schema._schema, parse(query), root_value=Query())
    assert result == standard_result.data


def test_strawberry_with_custom_resolvers():
    """Test JIT compilation with Strawberry custom field resolvers."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        posts {
            title
            wordCount
            author {
                displayName
            }
        }
    }
    """

    # Compile and execute with JIT
    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Query())

    # Check result
    assert result == snapshot(
        {
            "posts": [
                {
                    "title": "Introduction to GraphQL",
                    "wordCount": 14,
                    "author": {"displayName": "Alice (alice@example.com)"},
                },
                {
                    "title": "Understanding JIT Compilation",
                    "wordCount": 11,
                    "author": {"displayName": "Bob (bob@example.com)"},
                },
            ]
        }
    )

    # Compare with standard execution
    standard_result = execute(schema._schema, parse(query), root_value=Query())
    assert result == standard_result.data


def test_strawberry_single_field():
    """Test JIT compilation with single object field."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        featuredPost {
            title
            wordCount
            author {
                name
                displayName
            }
        }
    }
    """

    # Compile and execute with JIT
    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Query())

    # Check result - get the actual result first
    assert result == snapshot(
        {
            "featuredPost": {
                "title": "Featured: GraphQL Best Practices",
                "wordCount": 9,
                "author": {"name": "Alice", "displayName": "Alice (alice@example.com)"},
            }
        }
    )

    # Compare with standard execution
    standard_result = execute(schema._schema, parse(query), root_value=Query())
    assert result == standard_result.data


def test_strawberry_with_typename():
    """Test JIT compilation with __typename introspection."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        __typename
        posts {
            __typename
            id
            author {
                __typename
                name
            }
        }
    }
    """

    # Compile and execute with JIT
    compiled_fn = compile_query(schema._schema, query)
    result = compiled_fn(Query())

    # Check result
    assert result == snapshot(
        {
            "__typename": "Query",
            "posts": [
                {
                    "__typename": "Post",
                    "id": "1",
                    "author": {"__typename": "Author", "name": "Alice"},
                },
                {
                    "__typename": "Post",
                    "id": "2",
                    "author": {"__typename": "Author", "name": "Bob"},
                },
            ],
        }
    )

    # Compare with standard execution
    standard_result = execute(schema._schema, parse(query), root_value=Query())
    assert result == standard_result.data


def test_performance_comparison():
    """Compare performance between JIT and standard execution."""
    import time

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
        featuredPost {
            title
            author {
                displayName
            }
        }
    }
    """

    # Compile once
    compiled_fn = compile_query(schema._schema, query)
    parsed_query = parse(query)

    # Measure JIT execution time
    iterations = 1000
    root = Query()

    start = time.perf_counter()
    for _ in range(iterations):
        result = compiled_fn(root)
    jit_time = time.perf_counter() - start

    # Measure standard execution time
    start = time.perf_counter()
    for _ in range(iterations):
        result = execute(schema._schema, parsed_query, root_value=root)
    standard_time = time.perf_counter() - start

    # JIT should be significantly faster
    speedup = standard_time / jit_time
    print(f"\nPerformance comparison ({iterations} iterations):")
    print(f"  Standard execution: {standard_time:.3f}s")
    print(f"  JIT execution:      {jit_time:.3f}s")
    print(f"  Speedup:            {speedup:.1f}x")

    # Assert JIT is faster (at least 2x when using actual resolvers)
    # The speedup varies based on system load and resolver complexity
    assert speedup > 2, (
        f"JIT should be significantly faster, but only got {speedup:.1f}x speedup"
    )
