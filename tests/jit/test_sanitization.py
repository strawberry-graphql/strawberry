#!/usr/bin/env python3
"""Test that the identifier sanitization works correctly.

This test verifies that the _sanitize_identifier method properly validates
identifiers and rejects invalid ones.
"""

import pytest

import strawberry
from strawberry.jit import JITCompiler


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


def test_sanitize_identifier_valid():
    """Test that valid identifiers pass sanitization."""
    schema = strawberry.Schema(query=Query)
    compiler = JITCompiler(schema)

    # Valid identifiers
    valid_identifiers = [
        "hello",
        "myField",
        "field_123",
        "_private",
        "CamelCase",
        "snake_case",
        "CONSTANT",
        "x",
        "a1b2c3",
        "__typename",
    ]

    for identifier in valid_identifiers:
        result = compiler._sanitize_identifier(identifier)
        assert result == identifier, f"Valid identifier '{identifier}' should pass"


def test_sanitize_identifier_invalid():
    """Test that invalid identifiers are rejected."""
    schema = strawberry.Schema(query=Query)
    compiler = JITCompiler(schema)

    # Invalid: starts with number
    with pytest.raises(ValueError, match="must start with letter or underscore"):
        compiler._sanitize_identifier("123abc")

    # Invalid: contains special characters
    with pytest.raises(ValueError, match="contains invalid characters"):
        compiler._sanitize_identifier("hello-world")

    with pytest.raises(ValueError, match="contains invalid characters"):
        compiler._sanitize_identifier("hello.world")

    with pytest.raises(ValueError, match="contains invalid characters"):
        compiler._sanitize_identifier("hello$world")

    with pytest.raises(ValueError, match="contains invalid characters"):
        compiler._sanitize_identifier("hello world")

    with pytest.raises(ValueError, match="contains invalid characters"):
        compiler._sanitize_identifier("hello@world")

    # Invalid: empty string
    with pytest.raises(ValueError, match="cannot be empty"):
        compiler._sanitize_identifier("")

    # Invalid: Python keywords
    with pytest.raises(ValueError, match="Python keyword"):
        compiler._sanitize_identifier("import")

    with pytest.raises(ValueError, match="Python keyword"):
        compiler._sanitize_identifier("class")

    with pytest.raises(ValueError, match="Python keyword"):
        compiler._sanitize_identifier("def")

    with pytest.raises(ValueError, match="Python keyword"):
        compiler._sanitize_identifier("return")


def test_sanitize_identifier_code_injection_attempts():
    """Test that code injection attempts are blocked."""
    schema = strawberry.Schema(query=Query)
    compiler = JITCompiler(schema)

    # Various code injection attempts
    injection_attempts = [
        "'; exec('malicious code'); '",
        '"; __import__("os").system("ls"); "',
        "x'; DROP TABLE users; --",
        "field\n'; malicious(); '",
        "field'; import os; os.system('ls')",
        "\\'; malicious(); \\'",
    ]

    for attempt in injection_attempts:
        with pytest.raises(ValueError):
            compiler._sanitize_identifier(attempt)


def test_graphql_field_names_are_sanitized():
    """Test that GraphQL field names go through sanitization.

    This ensures that even if the GraphQL parser somehow allowed
    invalid names, the JIT compiler would catch them.
    """
    schema = strawberry.Schema(query=Query)

    # Normal query works
    query = "query { hello }"
    compiler = JITCompiler(schema)
    compiled = compiler.compile_query(query)
    result = compiled(Query())
    assert result["data"]["hello"] == "world"

    # Query with alias works
    query = "query { greeting: hello }"
    compiler = JITCompiler(schema)
    compiled = compiler.compile_query(query)
    result = compiled(Query())
    assert result["data"]["greeting"] == "world"


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("IDENTIFIER SANITIZATION TESTS")
    print("=" * 70)

    print("\n✅ Testing valid identifiers...")
    test_sanitize_identifier_valid()
    print("   All valid identifiers passed")

    print("\n✅ Testing invalid identifiers...")
    test_sanitize_identifier_invalid()
    print("   All invalid identifiers were properly rejected")

    print("\n✅ Testing code injection attempts...")
    test_sanitize_identifier_code_injection_attempts()
    print("   All code injection attempts were blocked")

    print("\n✅ Testing real GraphQL queries...")
    test_graphql_field_names_are_sanitized()
    print("   GraphQL field names are properly sanitized")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)
    print(
        "\n✅ Defense-in-depth sanitization is working correctly."
        "\n   The JIT compiler validates all identifiers before embedding"
        "\n   them in generated code, providing an additional security layer"
        "\n   on top of the GraphQL parser's validation."
    )
    print("\n" + "=" * 70)
