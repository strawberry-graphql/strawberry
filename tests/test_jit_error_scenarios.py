"""
Test various error handling scenarios in JIT compiler.
"""

from typing import Optional

import strawberry
from strawberry.jit import compile_query


@strawberry.type
class Item:
    id: int

    @strawberry.field
    def name(self) -> str:
        return f"Item {self.id}"

    @strawberry.field
    def error_field(self) -> Optional[str]:
        raise Exception(f"Error in item {self.id}")

    @strawberry.field
    def nullable_error(self) -> Optional[str]:
        raise Exception(f"Nullable error in item {self.id}")


@strawberry.type
class Container:
    @strawberry.field
    def items(self) -> list[Item]:
        return [Item(id=i) for i in range(3)]

    @strawberry.field
    def single_item(self) -> Item:
        return Item(id=99)


@strawberry.type
class Query:
    @strawberry.field
    def container(self) -> Container:
        return Container()


def test_list_errors():
    """Test error handling in list fields."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        container {
            items {
                id
                name
                nullableError
            }
        }
    }
    """

    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query())

    # Check that we have data for non-erroring fields
    items = result["data"]["container"]["items"]
    assert len(items) == 3
    for i, item in enumerate(items):
        assert item["id"] == i
        assert item["name"] == f"Item {i}"
        assert item["nullableError"] is None  # Errored field is None

    # Check that we have 3 errors (one per item)
    assert len(result["errors"]) == 3


def test_nested_errors():
    """Test error handling in nested structures."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        container {
            singleItem {
                id
                name
                errorField
            }
            items {
                id
                nullableError
            }
        }
    }
    """

    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query())

    # Non-nullable error field should still allow other fields
    single_item = result["data"]["container"]["singleItem"]
    assert single_item["id"] == 99
    assert single_item["name"] == "Item 99"

    # We should have errors for errorField and all nullableError fields
    assert len(result["errors"]) >= 4  # 1 for errorField + 3 for nullableError


def test_error_paths():
    """Test that error paths are correct."""
    schema = strawberry.Schema(Query)

    query = """
    query {
        container {
            items {
                id
                nullableError
            }
        }
    }
    """

    compiled_fn = compile_query(schema, query)
    result = compiled_fn(Query())

    errors = result.get("errors", [])

    # Check error paths
    for i, error in enumerate(errors):
        expected_path = ["container", "items", i, "nullableError"]
        assert error["path"] == expected_path, (
            f"Expected {expected_path}, got {error['path']}"
        )


if __name__ == "__main__":
    test_list_errors()
    test_nested_errors()
    test_error_paths()
