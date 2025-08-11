"""
Test JIT compilation with GraphQL built-in directives (@skip and @include).
"""

from pathlib import Path
from typing import List

from graphql import execute, parse
from pytest_snapshot.plugin import Snapshot

import strawberry
from strawberry.jit_compiler import GraphQLJITCompiler, compile_query
from strawberry.jit_compiler_optimized import compile_query_optimized

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
    published: bool
    views: int


@strawberry.type
class Query:
    @strawberry.field
    def posts(self) -> List[Post]:
        """Get all posts."""
        author1 = Author(id="a1", name="Alice", email="alice@example.com")
        author2 = Author(id="a2", name="Bob", email="bob@example.com")

        return [
            Post(
                id="p1",
                title="GraphQL Basics",
                content="Introduction to GraphQL",
                author=author1,
                published=True,
                views=100,
            ),
            Post(
                id="p2",
                title="Advanced GraphQL",
                content="Deep dive into GraphQL",
                author=author2,
                published=False,
                views=50,
            ),
        ]


def test_skip_directive(snapshot: Snapshot):
    """Test JIT compilation with @skip directive."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts($skipContent: Boolean!, $skipAuthor: Boolean!) {
        posts {
            id
            title
            content @skip(if: $skipContent)
            author @skip(if: $skipAuthor) {
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
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_directives"
    snapshot.assert_match(generated_code, "skip_directive.py")

    # Execute with skipping content
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root, variables={"skipContent": True, "skipAuthor": False})

    # Verify results
    assert len(result["posts"]) == 2
    assert "content" not in result["posts"][0]  # Content should be skipped
    assert "author" in result["posts"][0]  # Author should be included
    assert result["posts"][0]["author"]["name"] == "Alice"

    # Execute without skipping
    result2 = compiled_fn(root, variables={"skipContent": False, "skipAuthor": False})
    assert "content" in result2["posts"][0]  # Content should be included
    assert result2["posts"][0]["content"] == "Introduction to GraphQL"

    # Compare with standard GraphQL execution - use first result with same vars
    standard_result = execute(
        schema._schema,
        parse(query),
        root_value=root,
        variable_values={"skipContent": True, "skipAuthor": False},
    )
    assert result == standard_result.data


def test_include_directive(snapshot: Snapshot):
    """Test JIT compilation with @include directive."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts($includeViews: Boolean!, $includeEmail: Boolean!) {
        posts {
            id
            title
            views @include(if: $includeViews)
            author {
                name
                email @include(if: $includeEmail)
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
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_directives"
    snapshot.assert_match(generated_code, "include_directive.py")

    # Execute without including views
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root, variables={"includeViews": False, "includeEmail": True})

    # Verify results
    assert len(result["posts"]) == 2
    assert "views" not in result["posts"][0]  # Views should not be included
    assert result["posts"][0]["author"]["email"] == "alice@example.com"

    # Execute with including views
    result2 = compiled_fn(root, variables={"includeViews": True, "includeEmail": False})
    assert "views" in result2["posts"][0]  # Views should be included
    assert result2["posts"][0]["views"] == 100
    assert "email" not in result2["posts"][0]["author"]  # Email should not be included

    # Compare with standard GraphQL execution - use first result with same vars
    standard_result = execute(
        schema._schema,
        parse(query),
        root_value=root,
        variable_values={"includeViews": False, "includeEmail": True},
    )
    assert result == standard_result.data


def test_combined_directives(snapshot: Snapshot):
    """Test JIT compilation with both @skip and @include directives."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts($showDetails: Boolean!, $hidePublished: Boolean!) {
        posts {
            id
            title
            content @include(if: $showDetails)
            published @skip(if: $hidePublished)
            views @include(if: $showDetails)
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
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_directives"
    snapshot.assert_match(generated_code, "combined_directives.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    # Test with showing details but hiding published
    result = compiled_fn(
        root, variables={"showDetails": True, "hidePublished": True}
    )
    assert "content" in result["posts"][0]
    assert "views" in result["posts"][0]
    assert "published" not in result["posts"][0]

    # Test with hiding details but showing published
    result2 = compiled_fn(
        root, variables={"showDetails": False, "hidePublished": False}
    )
    assert "content" not in result2["posts"][0]
    assert "views" not in result2["posts"][0]
    assert "published" in result2["posts"][0]

    # Compare with standard GraphQL execution - use first result with same vars
    standard_result = execute(
        schema._schema,
        parse(query),
        root_value=root,
        variable_values={"showDetails": True, "hidePublished": True},
    )
    assert result == standard_result.data


def test_directives_with_fragments(snapshot: Snapshot):
    """Test JIT compilation with directives inside fragments."""
    schema = strawberry.Schema(Query)

    query = """
    fragment PostDetails on Post {
        content @include(if: $includeContent)
        published @skip(if: $skipPublished)
    }
    
    query GetPosts($includeContent: Boolean!, $skipPublished: Boolean!) {
        posts {
            id
            title
            ...PostDetails
        }
    }
    """

    # Compile the query
    compiler = GraphQLJITCompiler(schema._schema)
    document = parse(query)
    compiler._extract_fragments(document)
    operation = compiler._get_operation(document)
    root_type = schema._schema.type_map["Query"]

    # Generate the function code
    generated_code = compiler._generate_function(operation, root_type)

    # Check the generated code with snapshot
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_directives"
    snapshot.assert_match(generated_code, "directives_with_fragments.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()

    result = compiled_fn(
        root, variables={"includeContent": True, "skipPublished": False}
    )
    assert "content" in result["posts"][0]
    assert "published" in result["posts"][0]

    result2 = compiled_fn(
        root, variables={"includeContent": False, "skipPublished": True}
    )
    assert "content" not in result2["posts"][0]
    assert "published" not in result2["posts"][0]

    # Compare with standard GraphQL execution - use first result with same vars
    standard_result = execute(
        schema._schema,
        parse(query),
        root_value=root,
        variable_values={"includeContent": True, "skipPublished": False},
    )
    assert result == standard_result.data


def test_optimized_skip_directive():
    """Test optimized JIT compilation with @skip directive."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts($skipContent: Boolean!) {
        posts {
            id
            title
            content @skip(if: $skipContent)
            published
        }
    }
    """

    # Execute with optimized compiler
    compiled_fn = compile_query_optimized(schema._schema, query)
    root = Query()

    # Test skipping content
    result = compiled_fn(root, variables={"skipContent": True})
    assert len(result["posts"]) == 2
    assert "content" not in result["posts"][0]
    assert "published" in result["posts"][0]

    # Test not skipping content
    result2 = compiled_fn(root, variables={"skipContent": False})
    assert "content" in result2["posts"][0]
    assert result2["posts"][0]["content"] == "Introduction to GraphQL"

    # Compare with standard execution
    standard_result = execute(
        schema._schema,
        parse(query),
        root_value=root,
        variable_values={"skipContent": True},
    )
    assert result == standard_result.data


def test_optimized_include_directive():
    """Test optimized JIT compilation with @include directive."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts($includeAuthor: Boolean!) {
        posts {
            id
            title
            author @include(if: $includeAuthor) {
                name
            }
        }
    }
    """

    # Execute with optimized compiler
    compiled_fn = compile_query_optimized(schema._schema, query)
    root = Query()

    # Test not including author
    result = compiled_fn(root, variables={"includeAuthor": False})
    assert "author" not in result["posts"][0]

    # Test including author
    result2 = compiled_fn(root, variables={"includeAuthor": True})
    assert "author" in result2["posts"][0]
    assert result2["posts"][0]["author"]["name"] == "Alice"

    # Compare with standard execution
    standard_result = execute(
        schema._schema,
        parse(query),
        root_value=root,
        variable_values={"includeAuthor": True},
    )
    assert result2 == standard_result.data


def test_optimized_combined_directives():
    """Test optimized JIT with combined directives."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts($showExtra: Boolean!, $hideTitle: Boolean!) {
        posts {
            id
            title @skip(if: $hideTitle)
            views @include(if: $showExtra)
            published @include(if: $showExtra)
        }
    }
    """

    # Execute with optimized compiler
    compiled_fn = compile_query_optimized(schema._schema, query)
    root = Query()

    result = compiled_fn(root, variables={"showExtra": True, "hideTitle": False})
    assert "title" in result["posts"][0]
    assert "views" in result["posts"][0]
    assert "published" in result["posts"][0]

    result2 = compiled_fn(root, variables={"showExtra": False, "hideTitle": True})
    assert "title" not in result2["posts"][0]
    assert "views" not in result2["posts"][0]
    assert "published" not in result2["posts"][0]

    # Compare with standard execution
    standard_result = execute(
        schema._schema,
        parse(query),
        root_value=root,
        variable_values={"showExtra": True, "hideTitle": False},
    )
    assert result == standard_result.data


def test_literal_boolean_directives(snapshot: Snapshot):
    """Test JIT compilation with literal boolean values in directives."""
    schema = strawberry.Schema(Query)

    query = """
    query GetPosts {
        posts {
            id
            title
            content @skip(if: true)
            published @include(if: false)
            views @include(if: true)
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
    snapshot.snapshot_dir = HERE / "snapshots" / "jit_directives"
    snapshot.assert_match(generated_code, "literal_boolean_directives.py")

    # Execute the compiled function
    compiled_fn = compile_query(schema._schema, query)
    root = Query()
    result = compiled_fn(root)

    # Verify results
    assert "content" not in result["posts"][0]  # Skipped due to @skip(if: true)
    assert "published" not in result["posts"][0]  # Not included due to @include(if: false)
    assert "views" in result["posts"][0]  # Included due to @include(if: true)
    assert result["posts"][0]["views"] == 100

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

    test_skip_directive(snapshot)
    test_include_directive(snapshot)
    test_combined_directives(snapshot)
    test_directives_with_fragments(snapshot)
    test_literal_boolean_directives(snapshot)

    test_optimized_skip_directive()
    test_optimized_include_directive()
    test_optimized_combined_directives()

    print("\n✅ All directive JIT tests passed!")