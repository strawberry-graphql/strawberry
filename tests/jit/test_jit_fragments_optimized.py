"""
Test optimized JIT compilation with GraphQL fragments support.
"""

from graphql import execute, parse

import strawberry
from strawberry.jit import compile_query
from tests.jit.conftest import assert_jit_results_match


@strawberry.type
class Author:
    id: str
    name: str
    email: str


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
    published: bool


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> list[Post]:
        """Get all posts."""
        author1 = Author(id="a1", name="Alice", email="alice@example.com")
        author2 = Author(id="a2", name="Bob", email="bob@example.com")

        return [
            Post(
                id="p1",
                title="GraphQL Basics",
                content="Introduction to GraphQL",
                author=author1,
                comments=[
                    Comment(id="c1", text="Great post!", author=author2),
                    Comment(id="c2", text="Very helpful", author=author1),
                ],
                published=True,
            ),
            Post(
                id="p2",
                title="Advanced GraphQL",
                content="Deep dive into GraphQL",
                author=author2,
                comments=[
                    Comment(id="c3", text="Excellent!", author=author1),
                ],
                published=False,
            ),
        ]


def test_optimized_simple_fragment():
    """Test optimized JIT compilation with a simple fragment."""
    schema = strawberry.Schema(Query)

    query = """
    fragment PostFields on Post {
        id
        title
        content
    }

    query GetPosts {
        posts {
            ...PostFields
            author {
                name
            }
        }
    }
    """

    # Execute with optimized compiler
    compiled_fn = compile_query(schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["data"]["posts"]) == 2
    assert result["data"]["posts"][0]["id"] == "p1"
    assert result["data"]["posts"][0]["title"] == "GraphQL Basics"
    assert result["data"]["posts"][0]["content"] == "Introduction to GraphQL"
    assert result["data"]["posts"][0]["author"]["name"] == "Alice"

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert_jit_results_match(result, standard_result)


def test_optimized_nested_fragments():
    """Test optimized JIT compilation with nested fragments."""
    schema = strawberry.Schema(Query)

    query = """
    fragment AuthorInfo on Author {
        name
        email
    }

    fragment PostDetails on Post {
        id
        title
        content
        author {
            ...AuthorInfo
        }
    }

    query GetPostsWithDetails {
        posts {
            ...PostDetails
            published
        }
    }
    """

    # Execute with optimized compiler
    compiled_fn = compile_query(schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["data"]["posts"]) == 2
    assert result["data"]["posts"][0]["author"]["name"] == "Alice"
    assert result["data"]["posts"][0]["author"]["email"] == "alice@example.com"

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert_jit_results_match(result, standard_result)


def test_optimized_inline_fragment():
    """Test optimized JIT compilation with inline fragments."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPostsWithInline {
        posts {
            id
            title
            ... on Post {
                content
                published
                author {
                    name
                }
            }
        }
    }
    """

    # Execute with optimized compiler
    compiled_fn = compile_query(schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["data"]["posts"]) == 2
    assert "content" in result["data"]["posts"][0]
    assert "published" in result["data"]["posts"][0]
    assert result["data"]["posts"][0]["author"]["name"] == "Alice"

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert_jit_results_match(result, standard_result)


def test_optimized_multiple_fragments():
    """Test optimized JIT compilation with multiple fragments on same query."""
    schema = strawberry.Schema(Query)

    query = """
    fragment BasicFields on Post {
        id
        title
    }

    fragment DetailedFields on Post {
        content
        published
        comments {
            id
            text
            author {
                name
            }
        }
    }

    query GetPostsMultipleFragments {
        posts {
            ...BasicFields
            ...DetailedFields
            author {
                name
            }
        }
    }
    """

    # Execute with optimized compiler
    compiled_fn = compile_query(schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["data"]["posts"]) == 2
    assert result["data"]["posts"][0]["id"] == "p1"
    assert result["data"]["posts"][0]["title"] == "GraphQL Basics"
    assert result["data"]["posts"][0]["content"] == "Introduction to GraphQL"
    assert len(result["data"]["posts"][0]["comments"]) == 2
    assert result["data"]["posts"][0]["comments"][0]["text"] == "Great post!"

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert_jit_results_match(result, standard_result)


if __name__ == "__main__":
    test_optimized_simple_fragment()
    test_optimized_nested_fragments()
    test_optimized_inline_fragment()
    test_optimized_multiple_fragments()
    print("\n✅ All optimized fragment JIT tests passed!")
