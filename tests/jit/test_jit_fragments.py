"""
Test JIT compilation with GraphQL fragments support.
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
    bio: str


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
    comments: List[Comment]
    published: bool


@strawberry.type
class Video:
    id: str
    title: str
    url: str
    duration: int
    author: Author


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> List[Post]:
        """Get all posts."""
        author1 = Author(
            id="a1", name="Alice", email="alice@example.com", bio="Tech writer"
        )
        author2 = Author(id="a2", name="Bob", email="bob@example.com", bio="Developer")

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

    @strawberry.field
    def videos(self) -> List[Video]:
        """Get all videos."""
        author = Author(
            id="a3", name="Charlie", email="charlie@example.com", bio="Video creator"
        )

        return [
            Video(
                id="v1",
                title="GraphQL Tutorial",
                url="https://example.com/video1",
                duration=1200,
                author=author,
            ),
            Video(
                id="v2",
                title="Building APIs",
                url="https://example.com/video2",
                duration=1800,
                author=author,
            ),
        ]


def test_simple_fragment(snapshot: Snapshot):
    """Test JIT compilation with a simple fragment."""
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

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    compiler._extract_fragments(document)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_fragments"
    snapshot.assert_match(generated_code, "simple_fragment.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["posts"]) == 2
    assert result["posts"][0]["id"] == "p1"
    assert result["posts"][0]["title"] == "GraphQL Basics"
    assert result["posts"][0]["content"] == "Introduction to GraphQL"
    assert result["posts"][0]["author"]["name"] == "Alice"

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_nested_fragments(snapshot: Snapshot):
    """Test JIT compilation with nested fragments."""
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

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    compiler._extract_fragments(document)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_fragments"
    snapshot.assert_match(generated_code, "nested_fragments.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["posts"]) == 2
    assert result["posts"][0]["author"]["name"] == "Alice"
    assert result["posts"][0]["author"]["email"] == "alice@example.com"

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_inline_fragment(snapshot: Snapshot):
    """Test JIT compilation with inline fragments."""
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

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_fragments"
    snapshot.assert_match(generated_code, "inline_fragment.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["posts"]) == 2
    assert "content" in result["posts"][0]
    assert "published" in result["posts"][0]
    assert result["posts"][0]["author"]["name"] == "Alice"

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_multiple_fragments(snapshot: Snapshot):
    """Test JIT compilation with multiple fragments on same query."""
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
                bio
            }
        }
    }
    """

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    compiler._extract_fragments(document)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_fragments"
    snapshot.assert_match(generated_code, "multiple_fragments.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["posts"]) == 2
    assert result["posts"][0]["id"] == "p1"
    assert result["posts"][0]["title"] == "GraphQL Basics"
    assert result["posts"][0]["content"] == "Introduction to GraphQL"
    assert len(result["posts"][0]["comments"]) == 2
    assert result["posts"][0]["comments"][0]["text"] == "Great post!"

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_fragment_with_variables(snapshot: Snapshot):
    """Test JIT compilation with fragments and variables."""
    schema = strawberry.Schema(Query)

    # For now, this is a simple test since full variable support in fragments
    # would require more complex implementation
    query = """
    fragment PostInfo on Post {
        id
        title
        published
    }

    query GetPosts {
        posts {
            ...PostInfo
        }
    }
    """

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    compiler._extract_fragments(document)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_fragments"
    snapshot.assert_match(generated_code, "fragment_with_variables.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["posts"]) == 2
    assert result["posts"][0]["id"] == "p1"
    assert result["posts"][0]["published"] == True

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


def test_fragment_on_list(snapshot: Snapshot):
    """Test JIT compilation with fragments applied to list fields."""
    schema = strawberry.Schema(Query)

    query = """
    fragment CommentFields on Comment {
        id
        text
        author {
            name
        }
    }

    query GetPostsWithComments {
        posts {
            id
            title
            comments {
                ...CommentFields
            }
        }
    }
    """

    # Compile the query
    compiler = JITCompiler(schema._schema)
    document = parse(query)
    compiler._extract_fragments(document)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_fragments"
    snapshot.assert_match(generated_code, "fragment_on_list.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert len(result["posts"]) == 2
    assert len(result["posts"][0]["comments"]) == 2
    assert result["posts"][0]["comments"][0]["id"] == "c1"
    assert result["posts"][0]["comments"][0]["text"] == "Great post!"
    assert result["posts"][0]["comments"][0]["author"]["name"] == "Bob"

    # Compare with standard GraphQL execution
    standard_result = execute(schema._schema, parse(query), root_value=root)
    assert result == standard_result.data


if __name__ == "__main__":
    from pytest_snapshot.plugin import Snapshot

    # Create a mock snapshot for testing
    class MockSnapshot:
        def __init__(self):
            self.snapshot_dir = None

        def assert_match(self, content, filename):
            print(
                f"Would save snapshot to: {self.snapshot_dir / filename if self.snapshot_dir else filename}"
            )

    snapshot = MockSnapshot()

    test_simple_fragment(snapshot)
    test_nested_fragments(snapshot)
    test_inline_fragment(snapshot)
    test_multiple_fragments(snapshot)
    test_fragment_with_variables(snapshot)
    test_fragment_on_list(snapshot)
    print("\n✅ All fragment JIT tests passed!")
