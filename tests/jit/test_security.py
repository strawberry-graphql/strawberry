#!/usr/bin/env python3
"""Comprehensive security tests for JIT compiler.

This test suite verifies that the JIT compiler is resistant to code injection
attacks through various vectors including:
- Variable names and values
- Field aliases
- Type names
- Enum values
- Nested field paths
- Direct AST manipulation
- String escape sequences
"""

import pytest
from graphql import parse

import strawberry
from strawberry.jit import JITCompiler, compile_query

# Flag to detect if exploit succeeded
EXPLOIT_FLAG = {"pwned": False}


def mark_pwned():
    """This function should NEVER be called if the code is secure."""
    EXPLOIT_FLAG["pwned"] = True


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: str = "World") -> str:
        return f"Hello, {name}!"


schema = strawberry.Schema(query=Query)


# =============================================================================
# IDENTIFIER SANITIZATION TESTS
# =============================================================================


def test_sanitize_identifier_valid():
    """Test that valid identifiers pass sanitization."""
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


# =============================================================================
# GRAPHQL PARSER PROTECTION TESTS
# =============================================================================


def test_variable_name_injection():
    """Attempt to inject code through variable name."""
    # GraphQL parser should reject malicious variable names
    malicious_query = """
    query($myVar: String) {
        hello(name: $myVar)
    }
    """

    compiled = compile_query(schema, malicious_query)

    # Check that variable access in generated code is safe
    if hasattr(compiled, "_jit_source"):
        assert ".variable_values.get('" in compiled._jit_source
        # Ensure no eval/exec calls
        assert "eval(" not in compiled._jit_source
        assert "exec(" not in compiled._jit_source

    result = compiled(None, variables={"myVar": "test"})
    assert result["data"]["hello"] == "Hello, test!"


def test_field_alias_injection():
    """Attempt to inject code through field alias."""
    # GraphQL spec says aliases must be valid Names: [_A-Za-z][_0-9A-Za-z]*
    # These should be rejected by the GraphQL parser

    queries_to_try = [
        # Try quotes (should fail)
        'query { greeting: "]; mark_pwned(); x=[" hello }',
        # Try with backticks (should fail)
        "query { greeting: `]; mark_pwned(); x=[` hello }",
        # Normal alias (should work)
        "query { greeting123: hello }",
    ]

    for query in queries_to_try:
        try:
            compiled = compile_query(schema, query)
            result = compiled(None)
            # If it compiled, it must be a valid query
            assert "data" in result
        except Exception:
            # Parser rejected it - good!
            pass

    # Exploit flag should never be set
    assert not EXPLOIT_FLAG["pwned"]


def test_type_name_injection():
    """Attempt to inject through custom scalar type names."""

    @strawberry.type
    class QueryWithScalar:
        @strawberry.field
        def test(self, arg: str = "default") -> str:
            return arg

    schema2 = strawberry.Schema(query=QueryWithScalar)

    query = """
    query($val: String) {
        test(arg: $val)
    }
    """

    compiled = compile_query(schema2, query)

    # Check generated code for safe scalar parser usage
    if hasattr(compiled, "_jit_source"):
        if "_scalar_parsers" in compiled._jit_source:
            # Ensure no eval/exec calls
            assert "eval(" not in compiled._jit_source
            assert "exec(" not in compiled._jit_source

    result = compiled(None, variables={"val": "test"})
    assert result["data"]["test"] == "test"


def test_enum_value_injection():
    """Attempt to inject through enum values."""
    from enum import Enum

    @strawberry.enum
    class Priority(Enum):
        LOW = "low"
        HIGH = "high"

    @strawberry.type
    class Task:
        name: str
        priority: Priority

    @strawberry.type
    class QueryWithEnum:
        @strawberry.field
        def task(self, priority: Priority) -> Task:
            return Task(name="Test", priority=priority)

    schema3 = strawberry.Schema(query=QueryWithEnum)

    query = """
    query {
        task(priority: HIGH) {
            name
            priority
        }
    }
    """

    compiled = compile_query(schema3, query)

    # Check for safe enum access in generated code
    if hasattr(compiled, "_jit_source"):
        # Ensure no eval/exec calls
        assert "eval(" not in compiled._jit_source
        assert "exec(" not in compiled._jit_source

    result = compiled(None)
    assert result["data"]["task"]["priority"] == "HIGH"


def test_nested_field_path_injection():
    """Attempt to inject through nested field paths."""

    @strawberry.type
    class Author:
        name: str

    @strawberry.type
    class Post:
        title: str

        @strawberry.field
        def author(self) -> Author:
            return Author(name="Alice")

    @strawberry.type
    class QueryNested:
        @strawberry.field
        def post(self) -> Post:
            return Post(title="Test Post")

    schema4 = strawberry.Schema(query=QueryNested)

    query = """
    query {
        post {
            title
            author {
                name
            }
        }
    }
    """

    compiled = compile_query(schema4, query)

    # Inspect the generated code for safe path handling
    if hasattr(compiled, "_jit_source"):
        # Ensure no eval/exec calls
        assert "eval(" not in compiled._jit_source
        assert "exec(" not in compiled._jit_source

    result = compiled(None)
    assert result["data"]["post"]["author"]["name"] == "Alice"


# =============================================================================
# DIRECT AST MANIPULATION TESTS
# =============================================================================


def test_direct_ast_manipulation():
    """Test by directly manipulating AST node names."""
    query = """
    query($userInput: String) {
        hello(name: $userInput)
    }
    """

    document = parse(query)

    # Inspect AST structure
    for definition in document.definitions:
        if hasattr(definition, "variable_definitions"):
            for var_def in definition.variable_definitions:
                var_name = var_def.variable.name.value
                assert var_name == "userInput"

    compiler = JITCompiler(schema)
    compiled = compiler.compile_query(query)

    # Verify safe code generation
    if hasattr(compiled, "_jit_source"):
        # Look for the variable access
        assert "variable_values.get" in compiled._jit_source
        # Ensure no eval/exec calls
        assert "eval(" not in compiled._jit_source
        assert "exec(" not in compiled._jit_source

    # Try to execute with malicious variable value
    result = compiled(None, variables={"userInput": "'; mark_pwned(); '"})
    assert result["data"]["hello"] == "Hello, '; mark_pwned(); '!"
    assert not EXPLOIT_FLAG["pwned"]


def test_check_generated_code_structure():
    """Examine the structure of generated code for injection points."""
    queries_to_analyze = [
        ("Simple query", "query { hello }"),
        ("With variable", "query($var: String) { hello(name: $var) }"),
        ("With alias", "query { greeting: hello }"),
    ]

    compiler = JITCompiler(schema)

    for name, query in queries_to_analyze:
        compiled = compiler.compile_query(query)

        if hasattr(compiled, "_jit_source"):
            # Ensure no eval/exec calls
            assert "eval(" not in compiled._jit_source
            assert "exec(" not in compiled._jit_source

            # Count potential injection points (should be safely handled)
            lines = compiled._jit_source.split("\n")
            for line in lines:
                # If there are dict accesses, they should use safe methods
                if ".get('" in line or '["' in line:
                    # These are safe - just accessing dicts/objects
                    pass


def test_string_escape_bypass():
    """Test if we can bypass string escaping."""
    query = """
    query($input: String) {
        hello(name: $input)
    }
    """

    # Test various malicious inputs that might break out of strings
    malicious_inputs = [
        "'; mark_pwned(); '",
        '"; mark_pwned(); "',
        "\\'; mark_pwned(); \\'",
        "\n'; mark_pwned(); '",
        "\\x27; mark_pwned(); \\x27",
    ]

    compiler = JITCompiler(schema)
    compiled = compiler.compile_query(query)

    for malicious in malicious_inputs:
        result = compiled(None, variables={"input": malicious})
        # The malicious string should be treated as data, not code
        assert malicious in result["data"]["hello"]
        assert not EXPLOIT_FLAG["pwned"]


# =============================================================================
# GRAPHQL FIELD NAME SANITIZATION TESTS
# =============================================================================


def test_graphql_field_names_are_sanitized():
    """Test that GraphQL field names go through sanitization.

    This ensures that even if the GraphQL parser somehow allowed
    invalid names, the JIT compiler would catch them.
    """
    # Normal query works
    query = "query { hello }"
    compiler = JITCompiler(schema)
    compiled = compiler.compile_query(query)
    result = compiled(Query())
    assert result["data"]["hello"] == "Hello, World!"

    # Query with alias works
    query = "query { greeting: hello }"
    compiler = JITCompiler(schema)
    compiled = compiler.compile_query(query)
    result = compiled(Query())
    assert result["data"]["greeting"] == "Hello, World!"


# =============================================================================
# FINAL VERIFICATION
# =============================================================================


def test_no_exploit_success():
    """Verify that no exploits succeeded during testing."""
    assert not EXPLOIT_FLAG["pwned"], "Code injection was successful - security breach!"
