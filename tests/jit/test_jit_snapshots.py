"""
Test JIT compilation snapshots to inspect generated functions.
"""

import inspect

from strawberry.jit import compile_query


def get_jit_source(compiled_fn):
    """Extract the source code of a JIT-compiled function."""
    # Check if the function has the stored source code
    if hasattr(compiled_fn, "_jit_source"):
        return compiled_fn._jit_source
    return "Source code not available (compile with debug=True)"


def test_simple_query_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot of a simple query."""
    schema = jit_schema

    query = """
    query GetPosts {
        posts(limit: 2) {
            id
            title
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Get the generated code
    generated_code = get_jit_source(compiled_fn)

    # Verify the function works
    result = compiled_fn(query_type)
    assert len(result["data"]["posts"]) == 2
    assert result["data"]["posts"][0]["id"] == "p0"
    assert result["data"]["posts"][0]["title"] == "Post 0"

    # Snapshot the generated source code
    snapshot.assert_match(generated_code, "simple_query_source.py")


def test_nested_query_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot of a nested query."""
    schema = jit_schema

    query = """
    query GetPostsWithAuthor {
        posts(limit: 2) {
            id
            title
            author {
                id
                name
                email
            }
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Execute and verify
    result = compiled_fn(query_type)
    assert len(result["data"]["posts"]) == 2
    assert result["data"]["posts"][0]["author"]["name"] == "Alice"

    # Snapshot the generated source code
    generated_code = get_jit_source(compiled_fn)
    snapshot.assert_match(generated_code, "nested_query_source.py")


def test_query_with_variables_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot of a query with variables."""
    schema = jit_schema

    query = """
    query GetPosts($limit: Int!) {
        posts(limit: $limit) {
            id
            title
            published
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Execute with variables
    variables = {"limit": 3}
    result = compiled_fn(query_type, variables=variables)
    assert len(result["data"]["posts"]) == 3

    # Snapshot the generated source code
    generated_code = get_jit_source(compiled_fn)
    snapshot.assert_match(generated_code, "query_with_variables_source.py")


def test_query_with_directives_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot of a query with directives."""
    schema = jit_schema

    query = """
    query GetPosts($includeContent: Boolean!) {
        posts(limit: 2) {
            id
            title
            content @include(if: $includeContent)
            published @skip(if: false)
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Execute with variables
    variables = {"includeContent": True}
    result = compiled_fn(query_type, variables=variables)
    assert "content" in result["data"]["posts"][0]
    assert "published" in result["data"]["posts"][0]

    # Snapshot the generated source code
    generated_code = get_jit_source(compiled_fn)
    snapshot.assert_match(generated_code, "query_with_directives_source.py")


def test_query_with_fragments_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot of a query with fragments."""
    schema = jit_schema

    query = """
    fragment PostFields on Post {
        id
        title
        content
    }

    query GetPosts {
        posts(limit: 2) {
            ...PostFields
            author {
                name
            }
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Execute
    result = compiled_fn(query_type)
    assert "content" in result["data"]["posts"][0]
    assert result["data"]["posts"][0]["author"]["name"] == "Alice"

    # Snapshot the generated source code
    generated_code = get_jit_source(compiled_fn)
    snapshot.assert_match(generated_code, "query_with_fragments_source.py")


async def test_async_query_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot of an async query."""
    schema = jit_schema

    query = """
    query GetAsyncPosts {
        asyncPosts(limit: 2) {
            id
            title
            author {
                name
            }
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # The function should be async
    assert inspect.iscoroutinefunction(compiled_fn)

    # Execute
    result = await compiled_fn(query_type)
    assert len(result["data"]["asyncPosts"]) == 2

    # Snapshot the generated source code
    generated_code = get_jit_source(compiled_fn)
    snapshot.assert_match(generated_code, "async_query_source.py")


# Helper function to manually inspect generated code (for debugging)
def inspect_jit_function(query_string: str, schema=None):
    """
    Helper to inspect the generated JIT function.
    This can be used during development to see what's being generated.
    """
    if schema is None:
        schema = strawberry.Schema(Query)

    compiled_fn = compile_query(schema, query_string)

    print(f"Function name: {compiled_fn.__name__}")
    print(f"Is async: {inspect.iscoroutinefunction(compiled_fn)}")

    # Try to get any code we can
    if hasattr(compiled_fn, "__code__"):
        code = compiled_fn.__code__
        print(f"Code object: {code}")
        print(f"  - co_argcount: {code.co_argcount}")
        print(f"  - co_varnames: {code.co_varnames}")
        print(f"  - co_names: {code.co_names}")

    # If the JIT compiler stores the generated source somewhere, we could access it
    # For now, this is a placeholder for future enhancement

    return compiled_fn


if __name__ == "__main__":
    # Example of inspecting a generated function
    print("=" * 60)
    print("Inspecting simple query:")
    print("=" * 60)
    inspect_jit_function("""
        query {
            posts(limit: 2) {
                id
                title
            }
        }
    """)

    print("\n" + "=" * 60)
    print("Inspecting query with variables:")
    print("=" * 60)
    inspect_jit_function("""
        query GetPosts($limit: Int!) {
            posts(limit: $limit) {
                id
                title
            }
        }
    """)
