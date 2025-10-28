"""
Comprehensive non-null type handling tests for JIT compiler.

Based on GraphQL spec section on handling non-nullable types:
https://spec.graphql.org/October2021/#sec-Handling-Field-Errors

These tests ensure the JIT compiler correctly handles:
1. Nullable fields returning null
2. Non-null fields that error (propagate to parent)
3. Deep chains of non-null fields
4. Non-null arguments
5. Root-level non-null fields
"""

from typing import Optional

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import compile_query


# Test data classes for nullable scenarios
@strawberry.type
class DataType:
    """Test type with various nullable and non-null fields."""

    @strawberry.field
    def sync_nullable(self) -> Optional[str]:
        """Nullable field - returns None."""
        return None

    @strawberry.field
    def sync_non_null(self) -> str:
        """Non-nullable field - returns value."""
        return "value"

    @strawberry.field
    def sync_error_nullable(self) -> Optional[str]:
        """Nullable field that errors - should return null with error."""
        raise ValueError("Error in nullable field")

    @strawberry.field
    def sync_error_non_null(self) -> str:
        """Non-nullable field that errors - should propagate to parent."""
        raise ValueError("Error in non-null field")

    @strawberry.field
    def nested_nullable(self) -> Optional["DataType"]:
        """Returns nested instance."""
        return DataType()

    @strawberry.field
    def nested_non_null(self) -> "DataType":
        """Returns non-null nested instance."""
        return DataType()

    @strawberry.field
    def nested_error_nullable(self) -> Optional["DataType"]:
        """Nullable nested field that errors."""
        raise ValueError("Error in nested nullable")

    @strawberry.field
    def nested_error_non_null(self) -> "DataType":
        """Non-nullable nested field that errors."""
        raise ValueError("Error in nested non-null")


@strawberry.type
class Query:
    @strawberry.field
    def data(self) -> DataType:
        return DataType()

    @strawberry.field
    def data_non_null(self) -> DataType:
        """Non-null root field."""
        return DataType()

    @strawberry.field
    def error_non_null_root(self) -> str:
        """Non-null root field that errors."""
        raise ValueError("Error at root non-null")

    @strawberry.field
    def error_nullable_root(self) -> Optional[str]:
        """Nullable root field that errors."""
        raise ValueError("Error at root nullable")

    @strawberry.field
    def with_non_null_arg(self, required: str) -> str:
        """Field with non-null argument."""
        return f"Passed: {required}"

    @strawberry.field
    def with_nullable_arg(self, optional: Optional[str] = None) -> str:
        """Field with nullable argument."""
        return f"Value: {optional}"


def compare_results(jit_result, standard_result):
    """Compare JIT and standard execution results."""
    # Compare data
    assert jit_result.get("data") == standard_result.data, (
        f"Data mismatch:\nJIT: {jit_result.get('data')}\n"
        f"Standard: {standard_result.data}"
    )

    # Compare error presence
    jit_errors = jit_result.get("errors", [])
    std_errors = standard_result.errors or []

    assert len(jit_errors) == len(std_errors), (
        f"Error count mismatch:\nJIT: {len(jit_errors)} errors\n"
        f"Standard: {len(std_errors)} errors"
    )

    # Compare error messages and paths
    if jit_errors:
        for jit_err, std_err in zip(jit_errors, std_errors, strict=False):
            # Compare paths
            jit_path = jit_err.get("path", [])
            std_path = std_err.path or []
            assert jit_path == std_path, (
                f"Error path mismatch:\nJIT: {jit_path}\nStandard: {std_path}"
            )


def test_nullable_field_returns_null():
    """Test that nullable fields can return null without error."""
    schema = strawberry.Schema(Query)

    query = """
    {
        data {
            syncNullable
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    assert result.data == {"data": {"syncNullable": None}}
    assert not result.errors

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


def test_nullable_field_error_returns_null():
    """Test that errors in nullable fields return null with error."""
    schema = strawberry.Schema(Query)

    query = """
    {
        data {
            syncNonNull
            syncErrorNullable
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    assert result.data == {"data": {"syncNonNull": "value", "syncErrorNullable": None}}
    assert len(result.errors) == 1
    assert result.errors[0].path == ["data", "syncErrorNullable"]

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)

    compare_results(jit_result, result)


def test_non_null_field_error_propagates_to_parent():
    """Test that errors in non-null fields propagate to nearest nullable parent."""
    schema = strawberry.Schema(Query)

    query = """
    {
        data {
            syncErrorNonNull
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    # Parent becomes null because non-null child errored
    # Note: result.data is None (entire result nulled), not {"data": None}
    assert result.data is None
    assert len(result.errors) == 1
    assert result.errors[0].path == ["data", "syncErrorNonNull"]

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)

    compare_results(jit_result, result)


def test_deep_non_null_chain():
    """Test deep chain of non-null fields with error at bottom."""

    @strawberry.type
    class Level5:
        @strawberry.field
        def value(self) -> str:
            raise ValueError("Error at level 5")

    @strawberry.type
    class Level4:
        @strawberry.field
        def level5(self) -> Level5:  # Non-null
            return Level5()

    @strawberry.type
    class Level3:
        @strawberry.field
        def level4(self) -> Level4:  # Non-null
            return Level4()

    @strawberry.type
    class Level2:
        @strawberry.field
        def level3(self) -> Optional[Level3]:  # Nullable - error stops here
            return Level3()

    @strawberry.type
    class Level1:
        @strawberry.field
        def level2(self) -> Level2:  # Non-null
            return Level2()

    @strawberry.type
    class DeepQuery:
        @strawberry.field
        def level1(self) -> Level1:
            return Level1()

    schema = strawberry.Schema(DeepQuery)

    query = """
    {
        level1 {
            level2 {
                level3 {
                    level4 {
                        level5 {
                            value
                        }
                    }
                }
            }
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    # Error should propagate up to level3 (first nullable parent)
    assert result.data == {"level1": {"level2": {"level3": None}}}
    assert len(result.errors) == 1
    assert result.errors[0].path == [
        "level1",
        "level2",
        "level3",
        "level4",
        "level5",
        "value",
    ]

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)

    compare_results(jit_result, result)


def test_non_null_list_with_error():
    """Test non-null list where one item errors."""

    @strawberry.type
    class Item:
        id: int

        @strawberry.field
        def name(self) -> str:
            if self.id == 2:
                raise ValueError(f"Error in item {self.id}")
            return f"Item {self.id}"

    @strawberry.type
    class ListQuery:
        @strawberry.field
        def items(self) -> list[Item]:  # Non-null list
            return [Item(id=1), Item(id=2), Item(id=3)]

    schema = strawberry.Schema(ListQuery)

    query = """
    {
        items {
            id
            name
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    # List becomes null because non-null list item errored
    # Since items is at root level and is non-null, entire result is None
    assert result.data is None
    assert len(result.errors) == 1
    assert result.errors[0].path == ["items", 1, "name"]

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)

    compare_results(jit_result, result)


def test_nullable_list_with_non_null_items():
    """Test nullable list with non-null items where one errors."""

    @strawberry.type
    class Item:
        @strawberry.field
        def name(self) -> str:
            raise ValueError("Error in item")

    @strawberry.type
    class ListQuery:
        @strawberry.field
        def items(self) -> Optional[list[Item]]:  # Nullable list, non-null items
            return [Item(), Item()]

    schema = strawberry.Schema(ListQuery)

    query = """
    {
        items {
            name
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    # Entire list becomes null because items are non-null
    assert result.data == {"items": None}
    assert len(result.errors) == 1

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)

    compare_results(jit_result, result)


def test_non_null_list_with_nullable_items():
    """Test non-null list with nullable items where one errors."""

    @strawberry.type
    class Item:
        id: int

        @strawberry.field
        def name(self) -> Optional[str]:  # Nullable
            if self.id == 2:
                raise ValueError(f"Error in item {self.id}")
            return f"Item {self.id}"

    @strawberry.type
    class ListQuery:
        @strawberry.field
        def items(self) -> list[Item]:  # Non-null list
            return [Item(id=1), Item(id=2), Item(id=3)]

    schema = strawberry.Schema(ListQuery)

    query = """
    {
        items {
            id
            name
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    # List continues, but item 2's name is null
    expected = {
        "items": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": None},
            {"id": 3, "name": "Item 3"},
        ]
    }
    assert result.data == expected
    assert len(result.errors) == 1
    assert result.errors[0].path == ["items", 1, "name"]

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)

    compare_results(jit_result, result)


def test_root_level_non_null_field_error():
    """Test that error in root-level non-null field nulls entire result."""
    schema = strawberry.Schema(Query)

    query = """
    {
        errorNonNullRoot
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    # Entire result is null because root field is non-null
    assert result.data is None
    assert len(result.errors) == 1
    assert result.errors[0].path == ["errorNonNullRoot"]

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)

    compare_results(jit_result, result)


def test_multiple_errors_in_query():
    """Test that multiple errors are all collected."""
    schema = strawberry.Schema(Query)

    query = """
    {
        errorNullableRoot
        data {
            syncNonNull
            syncErrorNullable
        }
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    assert result.data == {
        "errorNullableRoot": None,
        "data": {"syncNonNull": "value", "syncErrorNullable": None},
    }
    assert len(result.errors) == 2

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)

    compare_results(jit_result, result)


def test_non_null_argument_with_value():
    """Test non-null argument succeeds when provided."""
    schema = strawberry.Schema(Query)

    query = """
    {
        withNonNullArg(required: "test")
    }
    """

    # Standard execution
    result = execute_sync(schema._schema, parse(query))
    assert result.data == {"withNonNullArg": "Passed: test"}
    assert not result.errors

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


def test_non_null_argument_with_variable():
    """Test non-null argument succeeds with variable."""
    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($value: String!) {
        withNonNullArg(required: $value)
    }
    """

    variables = {"value": "from_variable"}

    # Standard execution
    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"withNonNullArg": "Passed: from_variable"}
    assert not result.errors

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


def test_nullable_argument_with_null():
    """Test nullable argument accepts null."""
    schema = strawberry.Schema(Query)

    query = """
    query TestQuery($value: String) {
        withNullableArg(optional: $value)
    }
    """

    variables = {"value": None}

    # Standard execution
    result = execute_sync(schema._schema, parse(query), variable_values=variables)
    assert result.data == {"withNullableArg": "Value: None"}
    assert not result.errors

    # JIT execution
    compiled = compile_query(schema, query)
    jit_result = compiled(None, variables=variables)
    compare_results(jit_result, result)


if __name__ == "__main__":
    # Run all tests
    test_nullable_field_returns_null()

    test_nullable_field_error_returns_null()

    test_non_null_field_error_propagates_to_parent()

    test_deep_non_null_chain()

    test_non_null_list_with_error()

    test_nullable_list_with_non_null_items()

    test_non_null_list_with_nullable_items()

    test_root_level_non_null_field_error()

    test_multiple_errors_in_query()

    test_non_null_argument_with_value()

    test_non_null_argument_with_variable()

    test_nullable_argument_with_null()
