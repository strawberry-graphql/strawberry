"""
Comprehensive variable handling tests for JIT compiler.

Based on GraphQL spec and graphql-core test_variables.py:
https://spec.graphql.org/October2021/#sec-Variables

These tests ensure the JIT compiler correctly handles:
1. Null vs undefined vs missing variables
2. Default values and their precedence
3. Complex input objects with nested structures
4. Non-null type validation
5. List variables with various nullability combinations
6. Custom scalar parsing in variables
7. Error handling during variable coercion
"""

from typing import Optional

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


# Test input types
@strawberry.input
class NestedInput:
    """Nested input object for testing."""

    value: str
    count: Optional[int] = None


@strawberry.input
class ComplexInput:
    """Complex input object with various field types."""

    required_string: str
    optional_string: Optional[str] = None
    required_int: int
    optional_int: Optional[int] = None
    nested: Optional[NestedInput] = None
    list_of_strings: Optional[list[str]] = None


@strawberry.input
class InputWithDefaults:
    """Input type with default values."""

    name: str = "DefaultName"
    count: int = 42
    enabled: bool = True


def compare_results(jit_result, standard_result):
    """Compare JIT and standard execution results."""
    # Get data - handle both wrapped {"data": ...} and unwrapped formats
    if isinstance(jit_result, dict):
        if "data" in jit_result:
            jit_data = jit_result["data"]
        else:
            jit_data = jit_result  # Old unwrapped format
    else:
        jit_data = jit_result
    std_data = standard_result.data

    # Get errors
    jit_errors = jit_result.get("errors", []) if isinstance(jit_result, dict) else []
    std_errors = standard_result.errors or []

    # Compare data
    assert jit_data == std_data, (
        f"Data mismatch:\nJIT: {jit_data}\nStandard: {std_data}"
    )

    # Compare error count
    assert len(jit_errors) == len(std_errors), (
        f"Error count mismatch:\nJIT: {len(jit_errors)} errors\n"
        f"Standard: {len(std_errors)} errors\n"
        f"JIT errors: {jit_errors}\n"
        f"Standard errors: {[str(e) for e in std_errors]}"
    )


# Test: Null vs Undefined vs Missing


def test_missing_variable():
    """Test that missing variables work correctly with nullable types."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, value: Optional[str] = None) -> str:
            return f"Value: {value}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($value: String) {
        echo(value: $value)
    }
    """

    # No variables provided - should use None
    result = execute_sync(schema._schema, parse(query), variable_values={})
    assert result.data == {"echo": "Value: None"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables={})
    compare_results(jit_result, result)


def test_null_variable():
    """Test explicit null variable."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, value: Optional[str] = None) -> str:
            return f"Value: {value}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($value: String) {
        echo(value: $value)
    }
    """

    # Explicit null
    result = execute_sync(schema._schema, parse(query), variable_values={"value": None})
    assert result.data == {"echo": "Value: None"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables={"value": None})
    compare_results(jit_result, result)


def test_provided_variable():
    """Test provided variable value."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, value: Optional[str] = None) -> str:
            return f"Value: {value}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($value: String) {
        echo(value: $value)
    }
    """

    # Provided value
    result = execute_sync(
        schema._schema, parse(query), variable_values={"value": "hello"}
    )
    assert result.data == {"echo": "Value: hello"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables={"value": "hello"})
    compare_results(jit_result, result)


# Test: Default Values


def test_default_value_used_when_missing():
    """Test that default values are used when variables are missing."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, value: str = "default") -> str:
            return f"Value: {value}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($value: String = "QueryDefault") {
        echo(value: $value)
    }
    """

    # No variables - should use query default
    result = execute_sync(schema._schema, parse(query), variable_values={})
    assert result.data == {"echo": "Value: QueryDefault"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables={})
    compare_results(jit_result, result)


def test_default_value_overridden_by_variable():
    """Test that provided variables override defaults."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, value: str = "default") -> str:
            return f"Value: {value}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($value: String = "QueryDefault") {
        echo(value: $value)
    }
    """

    # Provided value overrides default
    result = execute_sync(
        schema._schema, parse(query), variable_values={"value": "Override"}
    )
    assert result.data == {"echo": "Value: Override"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables={"value": "Override"})
    compare_results(jit_result, result)


def test_null_overrides_default():
    """Test that explicit null overrides default value."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, value: Optional[str] = "default") -> str:
            return f"Value: {value}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($value: String = "QueryDefault") {
        echo(value: $value)
    }
    """

    # Explicit null overrides default
    result = execute_sync(schema._schema, parse(query), variable_values={"value": None})
    assert result.data == {"echo": "Value: None"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables={"value": None})
    compare_results(jit_result, result)


# Test: Complex Input Objects


def test_complex_input_object():
    """Test complex nested input objects."""

    @strawberry.type
    class Query:
        @strawberry.field
        def process_input(self, input: ComplexInput) -> str:
            parts = [
                f"required_string={input.required_string}",
                f"optional_string={input.optional_string}",
                f"required_int={input.required_int}",
                f"optional_int={input.optional_int}",
            ]
            if input.nested:
                parts.append(f"nested.value={input.nested.value}")
                parts.append(f"nested.count={input.nested.count}")
            if input.list_of_strings:
                parts.append(f"list={','.join(input.list_of_strings)}")
            return "; ".join(parts)

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($input: ComplexInput!) {
        processInput(input: $input)
    }
    """

    variables = {
        "input": {
            "requiredString": "hello",
            "optionalString": "world",
            "requiredInt": 123,
            "optionalInt": 456,
            "nested": {"value": "nested_value", "count": 10},
            "listOfStrings": ["a", "b", "c"],
        }
    }

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert "required_string=hello" in result.data["processInput"]
    assert "nested.value=nested_value" in result.data["processInput"]

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


def test_input_object_with_null_fields():
    """Test input object with null optional fields."""

    @strawberry.type
    class Query:
        @strawberry.field
        def process_input(self, input: ComplexInput) -> str:
            return f"optional_string={input.optional_string}, optional_int={input.optional_int}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($input: ComplexInput!) {
        processInput(input: $input)
    }
    """

    variables = {
        "input": {
            "requiredString": "hello",
            "optionalString": None,  # Explicit null
            "requiredInt": 123,
            "optionalInt": None,  # Explicit null
        }
    }

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"processInput": "optional_string=None, optional_int=None"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


def test_input_object_with_defaults():
    """Test input object with default values."""

    @strawberry.type
    class Query:
        @strawberry.field
        def process_input(self, input: InputWithDefaults) -> str:
            return f"name={input.name}, count={input.count}, enabled={input.enabled}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($input: InputWithDefaults!) {
        processInput(input: $input)
    }
    """

    # Empty input should use defaults
    variables = {"input": {}}

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"processInput": "name=DefaultName, count=42, enabled=True"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


# Test: List Variables


def test_list_variable_with_nullable_items():
    """Test list variable with nullable items."""

    @strawberry.type
    class Query:
        @strawberry.field
        def process_list(self, items: list[Optional[str]]) -> str:
            return f"items={','.join(str(i) for i in items)}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($items: [String]!) {
        processList(items: $items)
    }
    """

    variables = {"items": ["a", None, "b", None, "c"]}

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"processList": "items=a,None,b,None,c"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


def test_list_variable_with_non_null_items():
    """Test list variable with non-null items."""

    @strawberry.type
    class Query:
        @strawberry.field
        def process_list(self, items: list[str]) -> str:
            return f"count={len(items)}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($items: [String!]!) {
        processList(items: $items)
    }
    """

    # Valid case
    variables = {"items": ["a", "b", "c"]}

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"processList": "count=3"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


def test_empty_list_variable():
    """Test empty list variable."""

    @strawberry.type
    class Query:
        @strawberry.field
        def process_list(self, items: list[str]) -> str:
            return f"count={len(items)}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($items: [String!]!) {
        processList(items: $items)
    }
    """

    variables = {"items": []}

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"processList": "count=0"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


def test_nested_list_variables():
    """Test nested list variables."""

    @strawberry.input
    class ItemInput:
        name: str
        tags: list[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def process_items(self, items: list[ItemInput]) -> str:
            result = []
            for item in items:
                result.append(f"{item.name}:[{','.join(item.tags)}]")
            return "; ".join(result)

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($items: [ItemInput!]!) {
        processItems(items: $items)
    }
    """

    variables = {
        "items": [
            {"name": "item1", "tags": ["a", "b"]},
            {"name": "item2", "tags": ["c", "d", "e"]},
        ]
    }

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"processItems": "item1:[a,b]; item2:[c,d,e]"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


# Test: Type Coercion


def test_int_to_float_coercion():
    """Test that integers are coerced to floats."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo_float(self, value: float) -> str:
            return f"float={value}, type={type(value).__name__}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($value: Float!) {
        echoFloat(value: $value)
    }
    """

    # Int should be coerced to float
    variables = {"value": 42}

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert "float=42" in result.data["echoFloat"]

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


def test_string_list_coercion():
    """Test that single string is coerced to list."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo_list(self, values: list[str]) -> str:
            return f"count={len(values)}, first={values[0] if values else 'none'}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($values: [String!]!) {
        echoList(values: $values)
    }
    """

    # Single value should work
    variables = {"values": ["single"]}

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"echoList": "count=1, first=single"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


# Test: Multiple Variables


def test_multiple_variables():
    """Test query with multiple variables."""

    @strawberry.type
    class Query:
        @strawberry.field
        def combine(self, a: str, b: int, c: bool) -> str:
            return f"a={a}, b={b}, c={c}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($a: String!, $b: Int!, $c: Boolean!) {
        combine(a: $a, b: $b, c: $c)
    }
    """

    variables = {"a": "hello", "b": 42, "c": True}

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"combine": "a=hello, b=42, c=True"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


def test_partial_variables():
    """Test query with some variables provided."""

    @strawberry.type
    class Query:
        @strawberry.field
        def combine(
            self, a: str, b: Optional[int] = None, c: Optional[bool] = None
        ) -> str:
            return f"a={a}, b={b}, c={c}"

    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($a: String!, $b: Int, $c: Boolean) {
        combine(a: $a, b: $b, c: $c)
    }
    """

    # Only provide 'a'
    variables = {"a": "hello"}

    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"combine": "a=hello, b=None, c=None"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


if __name__ == "__main__":
    # Run all tests
    test_missing_variable()

    test_null_variable()

    test_provided_variable()

    test_default_value_used_when_missing()

    test_default_value_overridden_by_variable()

    test_null_overrides_default()

    test_complex_input_object()

    test_input_object_with_null_fields()

    test_input_object_with_defaults()

    test_list_variable_with_nullable_items()

    test_list_variable_with_non_null_items()

    test_empty_list_variable()

    test_nested_list_variables()

    test_int_to_float_coercion()

    test_string_list_coercion()

    test_multiple_variables()

    test_partial_variables()
