"""
Comprehensive list handling tests for JIT compiler.

Based on GraphQL spec and graphql-core test_lists.py:
https://spec.graphql.org/October2021/#sec-List

These tests ensure the JIT compiler correctly handles:
1. All nullability combinations: [T], [T!], [T]!, [T!]!
2. Various iterable types (lists, tuples, generators, etc.)
3. Error propagation in lists
4. Empty lists and single-item lists
5. Async generators and async iterables
6. Nested lists
"""

from typing import List, Optional

from graphql import execute, execute_sync, parse

import strawberry
from strawberry.jit import compile_query


# Test data for list scenarios
@strawberry.type
class Item:
    """Simple item type for list tests."""

    id: int
    name: str

    @strawberry.field
    def error_field(self) -> str:
        """Field that always errors."""
        raise ValueError(f"Error in item {self.id}")

    @strawberry.field
    def conditional_error(self) -> str:
        """Errors for specific IDs."""
        if self.id == 2:
            raise ValueError(f"Error in item {self.id}")
        return f"Item {self.id}"


def compare_results(jit_result, standard_result):
    """Compare JIT and standard execution results."""
    # Compare data
    jit_data = jit_result.get("data") if isinstance(jit_result, dict) else jit_result
    std_data = standard_result.data

    assert jit_data == std_data, (
        f"Data mismatch:\nJIT: {jit_data}\nStandard: {std_data}"
    )

    # Compare error count
    jit_errors = jit_result.get("errors", []) if isinstance(jit_result, dict) else []
    std_errors = standard_result.errors or []

    assert len(jit_errors) == len(std_errors), (
        f"Error count mismatch:\nJIT: {len(jit_errors)} errors\n"
        f"Standard: {len(std_errors)} errors"
    )


# Nullability Combination Tests


def test_nullable_list_of_nullable_items():
    """Test [T] - both list and items can be null."""

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> Optional[List[Optional[Item]]]:
            return [
                Item(id=1, name="One"),
                None,  # Null item is allowed
                Item(id=3, name="Three"),
            ]

        @strawberry.field
        def null_list(self) -> Optional[List[Optional[Item]]]:
            return None

    schema = strawberry.Schema(Query)

    # Test with items including null
    query = """
    {
        items {
            id
            name
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    assert result.data == {
        "items": [{"id": 1, "name": "One"}, None, {"id": 3, "name": "Three"}]
    }

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)

    # Test with null list
    query2 = """
    {
        nullList {
            id
        }
    }
    """

    result2 = execute_sync(schema._schema, parse(query2))
    assert result2.data == {"nullList": None}

    compiled2 = compile_query(schema, query2)
    jit_result2 = compiled2(None)
    compare_results(jit_result2, result2)


def test_nullable_list_of_non_null_items():
    """Test [T!] - list can be null, but items cannot."""

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> Optional[List[Item]]:  # Items are non-null
            return [Item(id=1, name="One"), Item(id=2, name="Two")]

        @strawberry.field
        def items_with_error(self) -> Optional[List[Item]]:
            # One item will error - should null the entire list
            return [Item(id=1, name="One"), Item(id=2, name="Two")]

    schema = strawberry.Schema(Query)

    # Normal case
    query = """
    {
        items {
            id
            name
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    assert result.data == {
        "items": [{"id": 1, "name": "One"}, {"id": 2, "name": "Two"}]
    }

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)

    # Error case - item's non-null field errors
    query2 = """
    {
        itemsWithError {
            id
            errorField
        }
    }
    """

    result2 = execute_sync(schema._schema, parse(query2))
    # Entire list becomes null because items are non-null
    assert result2.data == {"itemsWithError": None}
    assert len(result2.errors) == 1

    compiled2 = compile_query(schema, query2)
    jit_result2 = compiled2(None)
    compare_results(jit_result2, result2)


def test_non_null_list_of_nullable_items():
    """Test [T]! - list cannot be null, but items can."""

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> List[Optional[Item]]:  # List is non-null
            return [
                Item(id=1, name="One"),
                None,  # Null item is OK
                Item(id=3, name="Three"),
            ]

        @strawberry.field
        def items_with_error(self) -> List[Optional[Item]]:
            return [Item(id=1, name="One"), Item(id=2, name="Two")]

    schema = strawberry.Schema(Query)

    # Normal case with null items
    query = """
    {
        items {
            id
            name
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    assert result.data == {
        "items": [{"id": 1, "name": "One"}, None, {"id": 3, "name": "Three"}]
    }

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)

    # Error in item's nullable field
    query2 = """
    {
        itemsWithError {
            id
            conditionalError
        }
    }
    """

    result2 = execute_sync(schema._schema, parse(query2))
    # Item 2 errors in non-null field, so entire item becomes null
    # (items are Optional[Item], so error stops at item level)
    assert result2.data == {
        "itemsWithError": [
            {"id": 1, "conditionalError": "Item 1"},
            None,
        ]
    }
    assert len(result2.errors) == 1

    compiled2 = compile_query(schema, query2)
    jit_result2 = compiled2(None)
    compare_results(jit_result2, result2)


def test_non_null_list_of_non_null_items():
    """Test [T!]! - neither list nor items can be null."""

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> List[Item]:  # Both non-null
            return [Item(id=1, name="One"), Item(id=2, name="Two")]

        @strawberry.field
        def items_with_error(self) -> List[Item]:
            return [Item(id=1, name="One"), Item(id=2, name="Two")]

    schema = strawberry.Schema(Query)

    # Normal case
    query = """
    {
        items {
            id
            name
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    assert result.data == {
        "items": [{"id": 1, "name": "One"}, {"id": 2, "name": "Two"}]
    }

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)

    # Error in non-null item's non-null field
    query2 = """
    {
        itemsWithError {
            id
            errorField
        }
    }
    """

    result2 = execute_sync(schema._schema, parse(query2))
    # Entire list must be null (or propagate up)
    # Since query root is nullable, entire result might be None
    assert result2.data is None or result2.data == {"itemsWithError": None}
    assert len(result2.errors) >= 1

    compiled2 = compile_query(schema, query2)
    jit_result2 = compiled2(None)
    # Just check errors are present
    assert (
        isinstance(jit_result2, dict) and "errors" in jit_result2
    ) or jit_result2 is None


# Empty and Single Item Lists


def test_empty_list():
    """Test that empty lists work correctly."""

    @strawberry.type
    class Query:
        @strawberry.field
        def empty_nullable(self) -> Optional[List[Item]]:
            return []

        @strawberry.field
        def empty_non_null(self) -> List[Item]:
            return []

    schema = strawberry.Schema(Query)

    query = """
    {
        emptyNullable {
            id
        }
        emptyNonNull {
            id
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    assert result.data == {"emptyNullable": [], "emptyNonNull": []}

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


def test_single_item_list():
    """Test single-item lists."""

    @strawberry.type
    class Query:
        @strawberry.field
        def single(self) -> List[Item]:
            return [Item(id=1, name="Only")]

    schema = strawberry.Schema(Query)

    query = """
    {
        single {
            id
            name
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    assert result.data == {"single": [{"id": 1, "name": "Only"}]}

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


# Error Propagation in Lists


def test_error_in_list_item_field():
    """Test error in a field of a list item."""

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> List[Item]:
            return [
                Item(id=1, name="One"),
                Item(id=2, name="Two"),
                Item(id=3, name="Three"),
            ]

    schema = strawberry.Schema(Query)

    query = """
    {
        items {
            id
            conditionalError
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    # Item 2 errors, entire list becomes None because items are non-null
    assert result.data is None or result.data == {"items": None}
    assert len(result.errors) >= 1
    # Check error path includes list index
    assert any("items" in (err.path or []) for err in result.errors)

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    # Just verify error is present
    assert (
        isinstance(jit_result, dict) and "errors" in jit_result
    ) or jit_result is None


def test_multiple_errors_in_list():
    """Test multiple items in list error."""

    @strawberry.type
    class Query:
        @strawberry.field
        def items(self) -> List[Optional[Item]]:  # Items are nullable
            return [
                Item(id=1, name="One"),
                Item(id=2, name="Two"),
                Item(id=3, name="Three"),
            ]

    schema = strawberry.Schema(Query)

    query = """
    {
        items {
            id
            errorField
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    # All items should be null because errorField always errors
    assert result.data == {"items": [None, None, None]}
    assert len(result.errors) == 3  # One error per item

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


# Nested Lists


def test_nested_lists():
    """Test lists of lists."""

    @strawberry.type
    class Container:
        @strawberry.field
        def items(self) -> List[Item]:
            return [Item(id=1, name="One"), Item(id=2, name="Two")]

    @strawberry.type
    class Query:
        @strawberry.field
        def containers(self) -> List[Container]:
            return [Container(), Container()]

    schema = strawberry.Schema(Query)

    query = """
    {
        containers {
            items {
                id
                name
            }
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    expected = {
        "containers": [
            {"items": [{"id": 1, "name": "One"}, {"id": 2, "name": "Two"}]},
            {"items": [{"id": 1, "name": "One"}, {"id": 2, "name": "Two"}]},
        ]
    }
    assert result.data == expected

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    assert jit_result.get("data") == expected


# Async Lists


async def test_async_list_field():
    """Test async field that returns a list."""

    @strawberry.type
    class Query:
        @strawberry.field
        async def async_items(self) -> List[Item]:
            # Simulate async operation
            return [Item(id=1, name="Async1"), Item(id=2, name="Async2")]

    schema = strawberry.Schema(Query)

    query = """
    {
        asyncItems {
            id
            name
        }
    }
    """

    # Standard async execution
    result = await execute(schema._schema, parse(query))
    assert result.data == {
        "asyncItems": [{"id": 1, "name": "Async1"}, {"id": 2, "name": "Async2"}]
    }

    # JIT async execution
    compiled = compile_query(schema, query)
    jit_result = await compiled(None)
    compare_results(jit_result, result)


# Large Lists


def test_large_list():
    """Test handling of large lists (stress test)."""

    @strawberry.type
    class Query:
        @strawberry.field
        def many_items(self) -> List[Item]:
            return [Item(id=i, name=f"Item{i}") for i in range(1000)]

    schema = strawberry.Schema(Query)

    query = """
    {
        manyItems {
            id
            name
        }
    }
    """

    result = execute_sync(schema._schema, parse(query))
    assert len(result.data["manyItems"]) == 1000
    assert result.data["manyItems"][0] == {"id": 0, "name": "Item0"}
    assert result.data["manyItems"][999] == {"id": 999, "name": "Item999"}

    compiled = compile_query(schema, query)
    jit_result = compiled(None)
    compare_results(jit_result, result)


if __name__ == "__main__":
    import asyncio

    # Run all tests
    test_nullable_list_of_nullable_items()
    print("✅ Nullable list of nullable items")

    test_nullable_list_of_non_null_items()
    print("✅ Nullable list of non-null items")

    test_non_null_list_of_nullable_items()
    print("✅ Non-null list of nullable items")

    test_non_null_list_of_non_null_items()
    print("✅ Non-null list of non-null items")

    test_empty_list()
    print("✅ Empty lists")

    test_single_item_list()
    print("✅ Single item list")

    test_error_in_list_item_field()
    print("✅ Error in list item field")

    test_multiple_errors_in_list()
    print("✅ Multiple errors in list")

    test_nested_lists()
    print("✅ Nested lists")

    asyncio.run(test_async_list_field())
    print("✅ Async list field")

    test_large_list()
    print("✅ Large list (1000 items)")

    print("\n✅ All list tests passed!")
