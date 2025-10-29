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


async def test_parallel_async_query_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot showing parallel async execution with multiple async fields.

    This test demonstrates the key optimization where multiple independent async
    fields at the same level are executed in parallel using asyncio.gather().
    """
    schema = jit_schema

    # Query with MULTIPLE async fields at the same level - triggers parallel execution!
    query = """
    query ParallelAsyncFields {
        asyncPosts(limit: 1) {
            id
        }
        asyncUsers(limit: 1) {
            id
        }
        asyncComments(limit: 1) {
            id
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # The function should be async
    assert inspect.iscoroutinefunction(compiled_fn)

    # Execute
    result = await compiled_fn(query_type)

    # Verify all fields returned data
    assert "asyncPosts" in result["data"]
    assert "asyncUsers" in result["data"]
    assert "asyncComments" in result["data"]

    # Snapshot the generated source code
    generated_code = get_jit_source(compiled_fn)

    # Verify the code contains parallel execution markers
    assert "async_tasks" in generated_code, (
        "Should use async_tasks for parallel execution"
    )
    assert "asyncio.gather" in generated_code, (
        "Should use asyncio.gather() for parallel execution"
    )
    assert "task_asyncPosts" in generated_code, "Should create task for asyncPosts"
    assert "task_asyncUsers" in generated_code, "Should create task for asyncUsers"
    assert "task_asyncComments" in generated_code, (
        "Should create task for asyncComments"
    )

    snapshot.assert_match(generated_code, "parallel_async_query_source.py")


def test_nullable_field_error_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot of error handling in nullable field.

    When a nullable field errors, it should return null for that field
    and continue processing other fields.
    """
    schema = jit_schema

    query = """
    query GetPostWithError {
        posts(limit: 1) {
            id
            title
            errorField
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Execute and verify error handling
    result = compiled_fn(query_type)
    assert result["data"]["posts"][0]["id"] == "p0"
    assert result["data"]["posts"][0]["title"] == "Post 0"
    assert result["data"]["posts"][0]["errorField"] is None
    assert "errors" in result
    assert len(result["errors"]) > 0

    # Snapshot the generated source code
    generated_code = get_jit_source(compiled_fn)

    # Verify error handling code is present
    assert "try:" in generated_code, "Should have try/except for error handling"
    assert "except Exception" in generated_code, "Should catch exceptions"
    assert "errors.append" in generated_code, "Should collect errors"

    snapshot.assert_match(generated_code, "nullable_field_error_source.py")


def test_non_nullable_error_propagation_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot of error propagation in non-nullable field.

    When a non-nullable field errors, the error should propagate up
    the tree until it reaches a nullable boundary.
    """
    schema = jit_schema

    query = """
    query GetPostWithNonNullError {
        posts(limit: 1) {
            id
            nonNullErrorField
            title
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Execute and verify error propagation
    result = compiled_fn(query_type)
    # The error propagates all the way to the root - entire data becomes null
    assert result["data"] is None
    assert "errors" in result
    assert len(result["errors"]) > 0

    # Snapshot the generated source code
    generated_code = get_jit_source(compiled_fn)

    # Verify error handling code is present
    assert "try:" in generated_code, "Should have try/except for error handling"
    assert "except Exception" in generated_code, "Should catch exceptions"
    assert "errors.append" in generated_code, "Should collect errors"

    snapshot.assert_match(generated_code, "non_nullable_error_propagation_source.py")


async def test_multiple_errors_snapshot(snapshot, jit_schema, query_type):
    """Test snapshot of multiple fields erroring simultaneously.

    When multiple fields error, all errors should be collected and
    each field should handle its error independently.
    """
    schema = jit_schema

    query = """
    query GetMultipleErrors {
        posts(limit: 2) {
            id
            errorField
            anotherErrorField
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Execute and verify multiple error handling
    result = compiled_fn(query_type)
    assert result["data"]["posts"][0]["id"] == "p0"
    assert result["data"]["posts"][0]["errorField"] is None
    assert result["data"]["posts"][0]["anotherErrorField"] is None
    assert "errors" in result
    # Should have errors from both fields for the first post (limit: 2)
    assert len(result["errors"]) >= 2

    # Snapshot the generated source code
    generated_code = get_jit_source(compiled_fn)

    # Verify error handling code is present
    assert "try:" in generated_code, "Should have try/except for error handling"
    assert "except Exception" in generated_code, "Should catch exceptions"
    assert "errors.append" in generated_code, "Should collect errors"

    snapshot.assert_match(generated_code, "multiple_errors_source.py")
