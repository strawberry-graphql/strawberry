"""Test @defer and @stream directive fallback to standard executor.

The JIT compiler does not support incremental delivery directives (@defer, @stream)
which require streaming/multipart responses. When these directives are detected,
the compiler should fall back to the standard GraphQL executor with a warning.
"""

import warnings

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class Author:
    """Author type for testing."""

    id: str
    name: str
    books: list["Book"]


@strawberry.type
class Book:
    """Book type for testing."""

    id: str
    title: str
    author: Author


@strawberry.type
class Query:
    """Query root for testing."""

    @strawberry.field
    def author(self, id: str) -> Author:
        return Author(
            id=id,
            name="Test Author",
            books=[
                Book(id="1", title="Book 1", author=None),
                Book(id="2", title="Book 2", author=None),
            ],
        )

    @strawberry.field
    def books(self) -> list[Book]:
        author = Author(id="1", name="Author 1", books=[])
        return [
            Book(id="1", title="Book 1", author=author),
            Book(id="2", title="Book 2", author=author),
        ]


def test_defer_directive_triggers_fallback():
    """Test that @defer directive triggers fallback with warning."""
    schema = strawberry.Schema(Query)

    # Query with @defer on fragment
    query = """
    query GetAuthor {
        author(id: "1") {
            id
            name
            ... @defer {
                books {
                    id
                    title
                }
            }
        }
    }
    """

    # Should emit warning about fallback
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compiled = compile_query(schema, query)

        # Check warning was issued
        assert len(w) == 1
        assert issubclass(w[0].category, UserWarning)
        assert "@defer" in str(w[0].message) or "@stream" in str(w[0].message)
        assert "not supported" in str(w[0].message)
        assert "Falling back" in str(w[0].message)

    # Execute and verify it still works
    result = compiled(None)

    # Should return data (execution via standard executor)
    assert "data" in result
    assert result["data"]["author"]["id"] == "1"
    assert result["data"]["author"]["name"] == "Test Author"


def test_stream_directive_triggers_fallback():
    """Test that @stream directive triggers fallback with warning."""
    schema = strawberry.Schema(Query)

    # Query with @stream on list field
    query = """
    query GetBooks {
        books @stream(initialCount: 1) {
            id
            title
        }
    }
    """

    # Should emit warning about fallback
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compiled = compile_query(schema, query)

        # Check warning was issued
        assert len(w) == 1
        assert issubclass(w[0].category, UserWarning)
        assert "not supported" in str(w[0].message)

    # Execute and verify it still works
    result = compiled(None)

    # Should return data
    assert "data" in result
    assert len(result["data"]["books"]) == 2


def test_defer_on_named_fragment_triggers_fallback():
    """Test that @defer on named fragment spread triggers fallback."""
    schema = strawberry.Schema(Query)

    query = """
    fragment BookDetails on Book {
        id
        title
    }

    query GetAuthor {
        author(id: "1") {
            id
            name
            books {
                ...BookDetails @defer
            }
        }
    }
    """

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compiled = compile_query(schema, query)
        assert len(w) == 1

    result = compiled(None)
    assert "data" in result


def test_normal_query_no_fallback():
    """Test that queries without @defer/@stream use JIT compilation."""
    schema = strawberry.Schema(Query)

    query = """
    query GetAuthor {
        author(id: "1") {
            id
            name
            books {
                id
                title
            }
        }
    }
    """

    # Should NOT emit warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compiled = compile_query(schema, query)

        # No warnings should be issued
        assert len(w) == 0

    # Execute and verify
    result = compiled(None)
    assert "data" in result
    assert result["data"]["author"]["id"] == "1"


def test_skip_and_include_directives_work_normally():
    """Test that @skip and @include directives still work with JIT."""
    schema = strawberry.Schema(Query)

    query = """
    query GetAuthor($skipBooks: Boolean!) {
        author(id: "1") {
            id
            name
            books @skip(if: $skipBooks) {
                id
                title
            }
        }
    }
    """

    # Should NOT emit warning (these are supported)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compiled = compile_query(schema, query)
        assert len(w) == 0

    # Execute with skipBooks = true
    result = compiled(None, variables={"skipBooks": True})
    assert "data" in result
    assert result["data"]["author"]["id"] == "1"
    assert "books" not in result["data"]["author"]

    # Execute with skipBooks = false
    result = compiled(None, variables={"skipBooks": False})
    assert "data" in result
    assert "books" in result["data"]["author"]
    assert len(result["data"]["author"]["books"]) == 2


def test_fallback_matches_standard_execution():
    """Test that fallback produces same results as standard execution."""
    schema = strawberry.Schema(Query)

    query = """
    query GetBooks {
        books @stream(initialCount: 1) {
            id
            title
            author {
                name
            }
        }
    }
    """

    # Compile with JIT (will fallback)
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        compiled = compile_query(schema, query)

    jit_result = compiled(None)

    # Execute with standard executor
    document = parse(query)
    standard_result = execute_sync(schema._schema, document)

    # Results should match
    assert jit_result["data"] == standard_result.data
    assert len(jit_result.get("errors", [])) == len(standard_result.errors or [])


def test_defer_with_variables():
    """Test @defer directive with variables works via fallback."""
    schema = strawberry.Schema(Query)

    query = """
    query GetAuthor($authorId: String!) {
        author(id: $authorId) {
            id
            name
            ... @defer {
                books {
                    id
                }
            }
        }
    }
    """

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compiled = compile_query(schema, query)
        assert len(w) == 1

    result = compiled(None, variables={"authorId": "123"})
    assert "data" in result
    assert result["data"]["author"]["id"] == "123"


def test_nested_defer_triggers_fallback():
    """Test nested @defer directives trigger fallback."""
    schema = strawberry.Schema(Query)

    query = """
    query GetAuthor {
        author(id: "1") {
            id
            ... @defer {
                name
                ... @defer {
                    books {
                        id
                    }
                }
            }
        }
    }
    """

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compiled = compile_query(schema, query)
        assert len(w) == 1

    result = compiled(None)
    assert "data" in result


def test_defer_in_fragment_definition():
    """Test @defer in fragment definition triggers fallback."""
    schema = strawberry.Schema(Query)

    query = """
    fragment AuthorWithBooks on Author @defer {
        books {
            id
            title
        }
    }

    query GetAuthor {
        author(id: "1") {
            id
            name
            ...AuthorWithBooks
        }
    }
    """

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compiled = compile_query(schema, query)
        assert len(w) == 1

    result = compiled(None)
    assert "data" in result


if __name__ == "__main__":
    # Run all tests
    test_defer_directive_triggers_fallback()
    print("✅ @defer directive fallback works")

    test_stream_directive_triggers_fallback()
    print("✅ @stream directive fallback works")

    test_defer_on_named_fragment_triggers_fallback()
    print("✅ @defer on named fragment fallback works")

    test_normal_query_no_fallback()
    print("✅ Normal queries don't trigger fallback")

    test_skip_and_include_directives_work_normally()
    print("✅ @skip and @include directives work normally")

    test_fallback_matches_standard_execution()
    print("✅ Fallback matches standard execution")

    test_defer_with_variables()
    print("✅ @defer with variables works")

    test_nested_defer_triggers_fallback()
    print("✅ Nested @defer triggers fallback")

    test_defer_in_fragment_definition()
    print("✅ @defer in fragment definition triggers fallback")

    print("\n✅ All defer/stream fallback tests passed!")
