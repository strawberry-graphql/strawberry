"""
Test JIT compilation with GraphQL directives (@skip and @include).
"""

from graphql import execute, parse

from strawberry.jit import compile_query


def test_skip_directive_with_literal(jit_schema, query_type):
    """Test @skip directive with literal boolean."""
    schema = jit_schema

    # Skip should exclude the field
    query = """
    query {
        posts(limit: 2) {
            id
            title @skip(if: true)
            content @skip(if: false)
        }
    }
    """

    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(query_type)

    standard_result = execute(schema._schema, parse(query), root_value=query_type)

    assert jit_result == standard_result.data
    assert "title" not in jit_result["posts"][0]  # Skipped
    assert "content" in jit_result["posts"][0]  # Not skipped


def test_skip_directive_with_variable(jit_schema, query_type):
    """Test @skip directive with variable."""
    schema = jit_schema

    query = """
    query GetPosts($skipTitle: Boolean!, $skipContent: Boolean!) {
        posts(limit: 2) {
            id
            title @skip(if: $skipTitle)
            content @skip(if: $skipContent)
        }
    }
    """

    # Test skipping title but not content
    variables = {"skipTitle": True, "skipContent": False}

    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(query_type, variables=variables)

    standard_result = execute(
        schema._schema, parse(query), root_value=query_type, variable_values=variables
    )

    assert jit_result == standard_result.data
    assert "title" not in jit_result["posts"][0]
    assert "content" in jit_result["posts"][0]

    # Test not skipping either
    variables = {"skipTitle": False, "skipContent": False}
    jit_result = compiled_fn(query_type, variables=variables)

    assert "title" in jit_result["posts"][0]
    assert "content" in jit_result["posts"][0]


def test_include_directive_with_literal(jit_schema, query_type):
    """Test @include directive with literal boolean."""
    schema = jit_schema

    query = """
    query {
        posts(limit: 2) {
            id
            title @include(if: false)
            content @include(if: true)
            views
        }
    }
    """

    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(query_type)

    standard_result = execute(schema._schema, parse(query), root_value=query_type)

    assert jit_result == standard_result.data
    assert "title" not in jit_result["posts"][0]  # Not included
    assert "content" in jit_result["posts"][0]  # Included


def test_include_directive_with_variable(jit_schema, query_type):
    """Test @include directive with variable."""
    schema = jit_schema

    query = """
    query GetPosts($includeAuthor: Boolean!, $includeViews: Boolean!) {
        posts(limit: 2) {
            id
            title
            author @include(if: $includeAuthor) {
                id
                name
            }
            views @include(if: $includeViews)
        }
    }
    """

    # Include author but not views
    variables = {"includeAuthor": True, "includeViews": False}

    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(query_type, variables=variables)

    standard_result = execute(
        schema._schema, parse(query), root_value=query_type, variable_values=variables
    )

    assert jit_result == standard_result.data
    assert "author" in jit_result["posts"][0]
    assert "views" not in jit_result["posts"][0]


def test_combined_skip_and_include(jit_schema, query_type):
    """Test combining @skip and @include directives."""
    schema = jit_schema

    # Note: When both are present, field is included only if
    # @include is true AND @skip is false
    query = """
    query GetPosts($include: Boolean!, $skip: Boolean!) {
        posts(limit: 2) {
            id
            title @include(if: $include) @skip(if: $skip)
        }
    }
    """

    compiled_fn = compile_query(schema, query)

    # Test all combinations
    test_cases = [
        ({"include": True, "skip": False}, True),  # Include and don't skip -> show
        ({"include": True, "skip": True}, False),  # Include but skip -> hide
        ({"include": False, "skip": False}, False),  # Don't include -> hide
        ({"include": False, "skip": True}, False),  # Don't include and skip -> hide
    ]

    for variables, should_have_title in test_cases:
        jit_result = compiled_fn(query_type, variables=variables)
        standard_result = execute(
            schema._schema,
            parse(query),
            root_value=query_type,
            variable_values=variables,
        )

        assert jit_result == standard_result.data
        if should_have_title:
            assert "title" in jit_result["posts"][0]
        else:
            assert "title" not in jit_result["posts"][0]


def test_directives_on_nested_fields(jit_schema, query_type):
    """Test directives on nested fields."""
    schema = jit_schema

    query = """
    query GetPosts($skipAuthorName: Boolean!) {
        posts(limit: 2) {
            id
            title
            author {
                id
                name @skip(if: $skipAuthorName)
                verified
            }
        }
    }
    """

    variables = {"skipAuthorName": True}

    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(query_type, variables=variables)

    standard_result = execute(
        schema._schema, parse(query), root_value=query_type, variable_values=variables
    )

    assert jit_result == standard_result.data
    assert "name" not in jit_result["posts"][0]["author"]
    assert "verified" in jit_result["posts"][0]["author"]


def test_directives_with_fragments(jit_schema, query_type):
    """Test directives with fragments."""
    schema = jit_schema

    query = """
    fragment PostFields on Post {
        title @include(if: $includeTitle)
        content
    }

    query GetPosts($includeTitle: Boolean!) {
        posts(limit: 2) {
            id
            ...PostFields
            views @skip(if: false)
        }
    }
    """

    variables = {"includeTitle": False}

    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(query_type, variables=variables)

    standard_result = execute(
        schema._schema, parse(query), root_value=query_type, variable_values=variables
    )

    assert jit_result == standard_result.data
    assert "title" not in jit_result["posts"][0]  # Not included due to directive
    assert "content" in jit_result["posts"][0]  # From fragment
    assert "views" in jit_result["posts"][0]  # Not skipped


def test_directives_on_inline_fragments():
    """Test directives on inline fragments.

    Note: Directives on inline fragments (... @include/@skip) are not yet
    supported in the JIT compiler. This is a known limitation.
    """
    # TODO: Implement support for directives on inline fragments
    # For now, skip this test
    import pytest

    pytest.skip("Directives on inline fragments not yet supported in JIT")


def test_directive_on_root_field(jit_schema, query_type):
    """Test directives on root query fields."""
    schema = jit_schema

    query = """
    query GetData($includePosts: Boolean!, $includeFeatured: Boolean!) {
        posts(limit: 2) @include(if: $includePosts) {
            id
            title
        }
        featuredPost @include(if: $includeFeatured) {
            id
            title
        }
    }
    """

    variables = {"includePosts": True, "includeFeatured": False}

    compiled_fn = compile_query(schema, query)
    jit_result = compiled_fn(query_type, variables=variables)

    standard_result = execute(
        schema._schema, parse(query), root_value=query_type, variable_values=variables
    )

    assert jit_result == standard_result.data
    assert "posts" in jit_result
    assert "featuredPost" not in jit_result


def test_directives_performance(jit_schema, query_type):
    """Test performance with directives."""
    import time

    schema = jit_schema

    query = """
    query GetPosts($skipContent: Boolean!, $includeAuthor: Boolean!) {
        posts(limit: 20) {
            id
            title
            content @skip(if: $skipContent)
            author @include(if: $includeAuthor) {
                id
                name
            }
            views
        }
    }
    """

    variables = {"skipContent": True, "includeAuthor": False}

    # Compile once
    compiled_fn = compile_query(schema, query)
    parsed = parse(query)

    # Benchmark JIT
    start = time.time()
    for _ in range(100):
        jit_result = compiled_fn(query_type, variables=variables)
    jit_time = time.time() - start

    # Benchmark standard
    start = time.time()
    for _ in range(100):
        standard_result = execute(
            schema._schema, parsed, root_value=query_type, variable_values=variables
        )
    standard_time = time.time() - start

    print(f"Directives performance: {standard_time / jit_time:.1f}x faster with JIT")

    # JIT should still be faster even with directive conditions
    assert jit_time < standard_time
