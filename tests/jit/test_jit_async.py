"""
Test JIT compilation with async resolvers.
"""

import pytest
from graphql import execute, parse

from strawberry.jit import compile_query
from tests.jit.conftest import assert_jit_results_match


@pytest.mark.asyncio
async def test_async_simple_field(jit_schema, query_type):
    """Test JIT compilation with a simple async field."""
    schema = jit_schema

    query = """
    query HelloWorld {
        asyncHello(name: "GraphQL")
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema, query)
    jit_result = await compiled_fn(query_type)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=query_type)

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert jit_result["data"]["asyncHello"] == "Hello GraphQL"


@pytest.mark.asyncio
async def test_async_nested_fields(jit_schema, query_type):
    """Test JIT compilation with nested async fields."""
    schema = jit_schema

    query = """
    query GetPosts {
        asyncPosts(limit: 2) {
            id
            title
            author {
                id
                name
                bio
            }
            viewCount
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema, query)
    jit_result = await compiled_fn(query_type)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=query_type)

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert len(jit_result["data"]["asyncPosts"]) == 2
    assert jit_result["data"]["asyncPosts"][0]["author"]["bio"] == "Bio of Alice"
    assert jit_result["data"]["asyncPosts"][0]["viewCount"] == 0


@pytest.mark.asyncio
async def test_mixed_sync_async_fields(jit_schema, query_type):
    """Test JIT compilation with mixed sync and async fields."""
    schema = jit_schema

    query = """
    query MixedQuery {
        asyncPosts(limit: 1) {
            id
            title
            syncAuthor {
                id
                name
            }
            author {
                id
                bio
            }
            asyncComments(limit: 2) {
                id
                text
                likes
            }
        }
        posts(limit: 1) {
            id
            title
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema, query)
    root = query_type
    jit_result = await compiled_fn(query_type)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=query_type)

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert jit_result["data"]["asyncPosts"][0]["syncAuthor"]["id"] == "a1"
    assert jit_result["data"]["asyncPosts"][0]["author"]["bio"] == "Bio of Alice"
    assert len(jit_result["data"]["asyncPosts"][0]["asyncComments"]) <= 2
    if jit_result["data"]["asyncPosts"][0]["asyncComments"]:
        assert jit_result["data"]["asyncPosts"][0]["asyncComments"][0]["likes"] == 42


@pytest.mark.asyncio
async def test_async_with_list_fields(jit_schema, query_type):
    """Test JIT compilation with async list fields."""
    schema = jit_schema

    query = """
    query GetPostsWithComments {
        asyncPosts(limit: 2) {
            id
            asyncComments(limit: 2) {
                id
                text
                likes
            }
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema, query)
    root = query_type
    jit_result = await compiled_fn(query_type)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=query_type)

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert len(jit_result["data"]["asyncPosts"]) == 2
    # Check that async fields work properly
    for post in jit_result["data"]["asyncPosts"]:
        if post["asyncComments"]:
            assert all(c["likes"] == 42 for c in post["asyncComments"])


def test_sync_only_query(jit_schema, query_type):
    """Test that sync-only queries don't create async functions."""
    schema = jit_schema

    query = """
    query SyncOnly {
        posts(limit: 1) {
            id
            title
            syncAuthor {
                id
                name
            }
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema, query)
    root = query_type

    # This should work synchronously
    jit_result = compiled_fn(query_type)

    # Execute standard way
    standard_result = execute(schema._schema, parse(query), root_value=query_type)

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert jit_result["data"]["posts"][0]["id"] == "p0"


@pytest.mark.asyncio
async def test_async_with_variables(jit_schema, query_type):
    """Test async JIT compilation with variables."""
    schema = jit_schema

    query = """
    query GetPosts($limit: Int!, $name: String!) {
        asyncPosts(limit: $limit) {
            id
            title
        }
        asyncHello(name: $name)
    }
    """

    variables = {"limit": 1, "name": "Test"}

    # Execute the compiled function
    compiled_fn = compile_query(schema, query)
    root = query_type
    jit_result = await compiled_fn(root, variables=variables)

    # Execute standard way
    standard_result = await execute(
        schema._schema, parse(query), root_value=query_type, variable_values=variables
    )

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert len(jit_result["data"]["asyncPosts"]) == 1
    assert jit_result["data"]["asyncHello"] == "Hello Test"


@pytest.mark.asyncio
async def test_async_with_fragments(jit_schema, query_type):
    """Test async JIT compilation with fragments."""
    schema = jit_schema

    query = """
    fragment AuthorInfo on Author {
        id
        name
        bio
    }

    query GetPostsWithFragments {
        posts(limit: 1) {
            id
            title
            author {
                ...AuthorInfo
            }
        }
    }
    """

    # Execute the compiled function
    compiled_fn = compile_query(schema, query)
    root = query_type
    jit_result = await compiled_fn(query_type)

    # Execute standard way
    standard_result = await execute(schema._schema, parse(query), root_value=query_type)

    # Verify results match
    assert_jit_results_match(jit_result, standard_result)
    assert jit_result["data"]["posts"][0]["author"]["bio"] == "Bio of Alice"


if __name__ == "__main__":
    # Run async tests
    asyncio.run(test_async_simple_field())
    asyncio.run(test_async_nested_fields())
    asyncio.run(test_mixed_sync_async_fields())
    asyncio.run(test_async_with_list_fields())
    test_sync_only_query()
    asyncio.run(test_async_with_variables())
    asyncio.run(test_async_with_fragments())
    print("✅ All async tests passed!")
