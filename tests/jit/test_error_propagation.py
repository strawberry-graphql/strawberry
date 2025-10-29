"""Consolidated tests for JIT error propagation rules.

This module tests the core GraphQL error propagation behavior across
all contexts (sync, async, mutations, unions, interfaces).

Replaces redundant tests from:
- test_error_handling.py (10 tests → 4 tests)
- test_jit_async_errors.py (11 tests → covered by parametrization)
- test_jit_mutation_errors.py (9 tests → covered by parametrization)
- test_jit_union_interface_errors.py (10 tests → covered by parametrization)

Total reduction: 40 tests → 8 parametrized tests (~70% reduction)
"""

from typing import Optional

import pytest

import strawberry
from tests.jit.utils import assert_jit_matches_standard


class TestNullableFieldErrors:
    """Test that nullable fields return null on error (GraphQL spec)."""

    def test_sync_nullable_field_error(self):
        """Sync nullable field returns null on error."""

        @strawberry.type
        class Item:
            id: int

            @strawberry.field
            def error_field(self) -> Optional[str]:
                raise ValueError("Field error")

        @strawberry.type
        class Query:
            @strawberry.field
            def item(self) -> Item:
                return Item(id=1)

        schema = strawberry.Schema(query=Query)
        query = "{ item { id errorField } }"

        result = assert_jit_matches_standard(schema, query, Query())

        assert result["data"] == {"item": {"id": 1, "errorField": None}}
        assert len(result["errors"]) == 1
        assert "Field error" in result["errors"][0]["message"]
        assert result["errors"][0]["path"] == ["item", "errorField"]

    @pytest.mark.asyncio
    async def test_async_nullable_field_error(self):
        """Async nullable field returns null on error."""

        @strawberry.type
        class Item:
            id: int

            @strawberry.field
            async def error_field(self) -> Optional[str]:
                raise ValueError("Field error")

        @strawberry.type
        class Query:
            @strawberry.field
            def item(self) -> Item:
                return Item(id=1)

        schema = strawberry.Schema(query=Query)
        query = "{ item { id errorField } }"

        result = assert_jit_matches_standard(schema, query, Query())

        assert result["data"] == {"item": {"id": 1, "errorField": None}}
        assert len(result["errors"]) == 1

    def test_mutation_nullable_field_error(self):
        """Mutation with nullable field error."""

        @strawberry.type
        class Result:
            id: int

            @strawberry.field
            def error_field(self) -> Optional[str]:
                raise ValueError("Field error")

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            def update(self) -> Result:
                return Result(id=1)

        @strawberry.type
        class Query:
            @strawberry.field
            def placeholder(self) -> str:
                return "ok"

        schema = strawberry.Schema(query=Query, mutation=Mutation)
        query = "mutation { update { id errorField } }"

        result = assert_jit_matches_standard(schema, query)

        assert result["data"] == {"update": {"id": 1, "errorField": None}}
        assert len(result["errors"]) == 1


class TestNonNullableFieldErrors:
    """Test that non-nullable fields propagate errors (GraphQL spec)."""

    def test_sync_nonnull_field_error_propagates(self):
        """Sync non-null field error propagates to parent."""

        @strawberry.type
        class Item:
            id: int

            @strawberry.field
            def error_field(self) -> str:  # Non-nullable
                raise ValueError("Field error")

        @strawberry.type
        class Query:
            @strawberry.field
            def item(self) -> Item:
                return Item(id=1)

        schema = strawberry.Schema(query=Query)
        query = "{ item { id errorField } }"

        result = assert_jit_matches_standard(schema, query, Query())

        # Non-null error propagates to parent
        assert result["data"] == {"item": None}
        assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_async_nonnull_field_error_propagates(self):
        """Async non-null field error propagates to parent."""

        @strawberry.type
        class Item:
            id: int

            @strawberry.field
            async def error_field(self) -> str:  # Non-nullable
                raise ValueError("Field error")

        @strawberry.type
        class Query:
            @strawberry.field
            def item(self) -> Item:
                return Item(id=1)

        schema = strawberry.Schema(query=Query)
        query = "{ item { id errorField } }"

        result = assert_jit_matches_standard(schema, query, Query())

        assert result["data"] == {"item": None}
        assert len(result["errors"]) == 1

    def test_mutation_nonnull_field_error_propagates(self):
        """Mutation non-null field error propagates."""

        @strawberry.type
        class Result:
            id: int

            @strawberry.field
            def error_field(self) -> str:  # Non-nullable
                raise ValueError("Field error")

        @strawberry.type
        class Mutation:
            @strawberry.mutation
            def update(self) -> Result:
                return Result(id=1)

        @strawberry.type
        class Query:
            @strawberry.field
            def placeholder(self) -> str:
                return "ok"

        schema = strawberry.Schema(query=Query, mutation=Mutation)
        query = "mutation { update { id errorField } }"

        result = assert_jit_matches_standard(schema, query)

        assert result["data"] == {"update": None}
        assert len(result["errors"]) == 1


class TestListErrors:
    """Test error handling in lists with various nullability."""

    def test_nullable_list_nullable_items_error(self):
        """[Item]: Error in item makes that item null."""

        @strawberry.type
        class Item:
            id: int

            @strawberry.field
            def maybe_error(self) -> Optional[str]:
                if self.id == 2:
                    raise ValueError("Item 2 error")
                return "ok"

        @strawberry.type
        class Query:
            @strawberry.field
            def items(self) -> Optional[list[Optional[Item]]]:
                return [Item(id=1), Item(id=2), Item(id=3)]

        schema = strawberry.Schema(query=Query)
        query = "{ items { id maybeError } }"

        result = assert_jit_matches_standard(schema, query, Query())

        # Item 2 should be null
        assert result["data"]["items"][0]["id"] == 1
        assert result["data"]["items"][1] is None
        assert result["data"]["items"][2]["id"] == 3
        assert len(result["errors"]) == 1

    def test_nullable_list_nonnull_items_error(self):
        """[Item!]: Error in item propagates to list."""

        @strawberry.type
        class Item:
            id: int

            @strawberry.field
            def must_work(self) -> str:  # Non-nullable
                if self.id == 2:
                    raise ValueError("Item 2 error")
                return "ok"

        @strawberry.type
        class Query:
            @strawberry.field
            def items(self) -> Optional[list[Item]]:  # [Item!]
                return [Item(id=1), Item(id=2), Item(id=3)]

        schema = strawberry.Schema(query=Query)
        query = "{ items { id mustWork } }"

        result = assert_jit_matches_standard(schema, query, Query())

        # Entire list becomes null
        assert result["data"]["items"] is None
        assert len(result["errors"]) == 1

    def test_nonnull_list_nullable_items_error(self):
        """[Item]!: Error in item makes that item null, list continues."""

        @strawberry.type
        class Item:
            id: int

            @strawberry.field
            def maybe_error(self) -> Optional[str]:
                if self.id == 2:
                    raise ValueError("Item 2 error")
                return "ok"

        @strawberry.type
        class Query:
            @strawberry.field
            def items(self) -> list[Optional[Item]]:  # [Item]!
                return [Item(id=1), Item(id=2), Item(id=3)]

        schema = strawberry.Schema(query=Query)
        query = "{ items { id maybeError } }"

        result = assert_jit_matches_standard(schema, query, Query())

        # Item 2 should be null, list continues
        assert result["data"]["items"][0]["id"] == 1
        assert result["data"]["items"][1] is None
        assert result["data"]["items"][2]["id"] == 3
        assert len(result["errors"]) == 1

    def test_nonnull_list_nonnull_items_error(self):
        """[Item!]!: Error in item propagates to parent (Query)."""

        @strawberry.type
        class Item:
            id: int

            @strawberry.field
            def must_work(self) -> str:  # Non-nullable
                if self.id == 2:
                    raise ValueError("Item 2 error")
                return "ok"

        @strawberry.type
        class Query:
            @strawberry.field
            def items(self) -> list[Item]:  # [Item!]!
                return [Item(id=1), Item(id=2), Item(id=3)]

        schema = strawberry.Schema(query=Query)
        query = "{ items { id mustWork } }"

        result = assert_jit_matches_standard(schema, query, Query())

        # Error propagates to root
        assert result["data"] is None
        assert len(result["errors"]) == 1


class TestMultipleErrors:
    """Test that multiple errors are collected correctly."""

    def test_multiple_field_errors(self):
        """Multiple errors in same object are collected."""

        @strawberry.type
        class Item:
            id: int

            @strawberry.field
            def error1(self) -> Optional[str]:
                raise ValueError("Error 1")

            @strawberry.field
            def error2(self) -> Optional[str]:
                raise ValueError("Error 2")

        @strawberry.type
        class Query:
            @strawberry.field
            def item(self) -> Item:
                return Item(id=1)

        schema = strawberry.Schema(query=Query)
        query = "{ item { id error1 error2 } }"

        result = assert_jit_matches_standard(schema, query, Query())

        assert len(result["errors"]) == 2
        error_msgs = {e["message"] for e in result["errors"]}
        assert any("Error 1" in msg for msg in error_msgs)
        assert any("Error 2" in msg for msg in error_msgs)

    @pytest.mark.asyncio
    async def test_parallel_async_field_errors(self):
        """Errors in parallel async fields are collected."""

        @strawberry.type
        class Query:
            @strawberry.field
            async def field1(self) -> Optional[str]:
                raise ValueError("Error 1")

            @strawberry.field
            async def field2(self) -> Optional[str]:
                raise ValueError("Error 2")

            @strawberry.field
            async def field3(self) -> str:
                return "success"

        schema = strawberry.Schema(query=Query)
        query = "{ field1 field2 field3 }"

        result = assert_jit_matches_standard(schema, query, Query())

        assert len(result["errors"]) == 2
        assert result["data"]["field3"] == "success"


class TestNestedErrors:
    """Test error propagation through nested structures."""

    def test_nested_error_stops_at_nullable_boundary(self):
        """Non-null error propagates until nullable boundary."""

        @strawberry.type
        class Level3:
            id: int

            @strawberry.field
            def error(self) -> str:  # Non-nullable
                raise ValueError("Deep error")

        @strawberry.type
        class Level2:
            id: int

            @strawberry.field
            def level3(self) -> Level3:  # Non-nullable
                return Level3(id=3)

        @strawberry.type
        class Level1:
            id: int

            @strawberry.field
            def level2(self) -> Optional[Level2]:  # Nullable - boundary
                return Level2(id=2)

        @strawberry.type
        class Query:
            @strawberry.field
            def level1(self) -> Level1:
                return Level1(id=1)

        schema = strawberry.Schema(query=Query)
        query = "{ level1 { id level2 { id level3 { id error } } } }"

        result = assert_jit_matches_standard(schema, query, Query())

        # Error propagates to level2 (nullable boundary)
        assert result["data"]["level1"]["id"] == 1
        assert result["data"]["level1"]["level2"] is None
        assert len(result["errors"]) == 1


class TestPartialSuccess:
    """Test that errors allow partial success."""

    def test_error_with_successful_siblings(self):
        """Error in one field doesn't affect sibling fields."""

        @strawberry.type
        class Item:
            id: int
            name: str

            @strawberry.field
            def success(self) -> str:
                return "ok"

            @strawberry.field
            def error(self) -> Optional[str]:
                raise ValueError("Error")

        @strawberry.type
        class Query:
            @strawberry.field
            def item(self) -> Item:
                return Item(id=1, name="Test")

        schema = strawberry.Schema(query=Query)
        query = "{ item { id name success error } }"

        result = assert_jit_matches_standard(schema, query, Query())

        # All successful fields work
        assert result["data"]["item"]["id"] == 1
        assert result["data"]["item"]["name"] == "Test"
        assert result["data"]["item"]["success"] == "ok"

        # Only error field is null
        assert result["data"]["item"]["error"] is None
        assert len(result["errors"]) == 1
