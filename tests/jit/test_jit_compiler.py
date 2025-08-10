from inline_snapshot import external

"""
Tests for the GraphQL JIT compiler using Strawberry schemas.
"""

from typing import List

from graphql import execute, parse
from inline_snapshot import outsource, snapshot

import strawberry
from strawberry.jit_compiler import GraphQLJITCompiler, compile_query


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


def test_simple_query():
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

    # Check the generated code with external snapshot
    assert outsource(generated_code, suffix=".py") == snapshot(
        external("f727d3e40fdc*.py")
    )

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Check the result with inline snapshot
    assert result == snapshot(
        {
            "posts": [
                {"id": "1", "title": "First Post"},
                {"id": "2", "title": "Second Post"},
            ]
        }
    )

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_nested_query():
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

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Check the result with inline snapshot
    assert result == snapshot(
        {
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
    )

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_query_with_aliases():
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

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Check the result with inline snapshot
    assert result == snapshot(
        {
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
    )

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_query_with_typename():
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

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Check the result with inline snapshot
    assert result == snapshot(
        {
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
    )

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_custom_resolver():
    """Test JIT compilation with custom resolvers."""

    @strawberry.type
    class AuthorWithCustomField:
        id: str
        name: str
        email: str

        @strawberry.field
        def display_name(self) -> str:
            return f"{self.name} <{self.email}>"

    @strawberry.type
    class PostWithSummary:
        id: str
        title: str
        content: str
        author: AuthorWithCustomField

        @strawberry.field
        def summary(self) -> str:
            return f"{self.title}: {self.content[:20]}..."

    @strawberry.type
    class QueryWithCustom:
        @strawberry.field
        def posts(self) -> List[PostWithSummary]:
            return [
                PostWithSummary(
                    id="1",
                    title="First Post",
                    content="Hello World",
                    author=AuthorWithCustomField(
                        id="a1", name="Alice", email="alice@example.com"
                    ),
                ),
                PostWithSummary(
                    id="2",
                    title="Second Post",
                    content="GraphQL is great",
                    author=AuthorWithCustomField(
                        id="a2", name="Bob", email="bob@example.com"
                    ),
                ),
            ]

    schema = strawberry.Schema(QueryWithCustom)

    query = """
    query {
        posts {
            title
            summary
            author {
                displayName
            }
        }
    }
    """

    # Compile the query
    compiler = GraphQLJITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["QueryWithCustom"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with external snapshot
    assert outsource(generated_code, suffix=".py") == snapshot(
        external("aed6dc764a35*.py")
    )

    # The generated code should use resolvers
    assert "resolver" in generated_code
    assert "_resolvers" in generated_code

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = QueryWithCustom()
    result = compiled_fn(root)

    # Check the result with inline snapshot
    assert result == snapshot(
        {
            "posts": [
                {
                    "title": "First Post",
                    "summary": "First Post: Hello World...",
                    "author": {"displayName": "Alice <alice@example.com>"},
                },
                {
                    "title": "Second Post",
                    "summary": "Second Post: GraphQL is great...",
                    "author": {"displayName": "Bob <bob@example.com>"},
                },
            ]
        }
    )

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_list_handling():
    """Test that the JIT compiler correctly handles lists."""
    schema = strawberry.Schema(Query)

    # Test with actual list
    query = """
    query {
        posts {
            id
        }
    }
    """

    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    assert result == snapshot({"posts": [{"id": "1"}, {"id": "2"}]})

    # Compare with standard execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data

    # Test with empty list
    @strawberry.type
    class EmptyQuery:
        @strawberry.field
        def posts(self) -> List[Post]:
            return []

    empty_schema = strawberry.Schema(EmptyQuery)
    compiled_fn_empty = compile_query(empty_schema._schema, query)
    root_empty = EmptyQuery()
    result_empty = compiled_fn_empty(root_empty)
    assert result_empty == snapshot({"posts": []})

    standard_empty = execute(empty_schema._schema, parse(query), root_value=root_empty)
    assert result_empty == standard_empty.data


def test_single_object_field():
    """Test JIT compilation with single object field."""

    @strawberry.type
    class SinglePostQuery:
        @strawberry.field
        def featured_post(self) -> Post:
            return Post(
                id="3",
                title="Featured Post",
                content="This is featured",
                author=Author(id="a3", name="Charlie", email="charlie@example.com"),
            )

    schema = strawberry.Schema(SinglePostQuery)

    query = """
    query {
        featuredPost {
            id
            title
            author {
                name
            }
        }
    }
    """

    compiled_fn = compile_query(schema._schema, query)
    root = SinglePostQuery()
    result = compiled_fn(root)

    assert result == snapshot(
        {
            "featuredPost": {
                "id": "3",
                "title": "Featured Post",
                "author": {"name": "Charlie"},
            }
        }
    )

    # Compare with standard execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data
