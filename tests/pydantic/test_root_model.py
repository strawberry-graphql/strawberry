"""Tests for Pydantic v2 RootModel with Strawberry.

RootModel allows wrapping a single value in a model with validation.
This is useful for validating scalars, lists, or dicts with custom validation.
"""

from typing import Annotated

import pydantic
from pydantic import Field, RootModel

import strawberry


def test_root_model_with_list_in_resolver():
    """Test using RootModel to wrap a list with validation in a resolver."""

    class TagList(RootModel[list[str]]):
        """A validated list of tags."""

        def __iter__(self):
            return iter(self.root)

        def __len__(self):
            return len(self.root)

    @strawberry.type
    class Query:
        @strawberry.field
        def process_tags(self, tags: list[str]) -> list[str]:
            # Use RootModel for validation
            validated = TagList.model_validate(tags)
            return list(validated)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            processTags(tags: ["python", "graphql", "strawberry"])
        }
        """
    )

    assert not result.errors
    assert result.data["processTags"] == ["python", "graphql", "strawberry"]


def test_root_model_with_constrained_list():
    """Test RootModel with a constrained list (min/max items)."""

    class BoundedList(
        RootModel[Annotated[list[int], Field(min_length=1, max_length=5)]]
    ):
        """A list with 1-5 items."""

    @strawberry.type
    class Query:
        @strawberry.field
        def bounded_list(self, items: list[int]) -> list[int]:
            validated = BoundedList.model_validate(items)
            return validated.root

    schema = strawberry.Schema(query=Query)

    # Valid input
    result = schema.execute_sync(
        """
        query {
            boundedList(items: [1, 2, 3])
        }
        """
    )

    assert not result.errors
    assert result.data["boundedList"] == [1, 2, 3]

    # Too many items
    result = schema.execute_sync(
        """
        query {
            boundedList(items: [1, 2, 3, 4, 5, 6])
        }
        """
    )

    assert result.errors is not None
    assert "too_long" in result.errors[0].message


def test_root_model_with_dict():
    """Test RootModel wrapping a dictionary."""

    class StringDict(RootModel[dict[str, str]]):
        """A string-to-string dictionary."""

    @strawberry.type
    class Query:
        @strawberry.field
        def dict_values(self) -> list[str]:
            data = StringDict.model_validate({"key1": "value1", "key2": "value2"})
            return list(data.root.values())

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            dictValues
        }
        """
    )

    assert not result.errors
    assert set(result.data["dictValues"]) == {"value1", "value2"}


def test_root_model_with_scalar():
    """Test RootModel wrapping a scalar with constraints."""

    class PositiveInt(RootModel[Annotated[int, Field(gt=0)]]):
        """A positive integer wrapper."""

    @strawberry.type
    class Query:
        @strawberry.field
        def positive_value(self, value: int) -> int:
            validated = PositiveInt.model_validate(value)
            return validated.root

    schema = strawberry.Schema(query=Query)

    # Valid input
    result = schema.execute_sync(
        """
        query {
            positiveValue(value: 42)
        }
        """
    )

    assert not result.errors
    assert result.data["positiveValue"] == 42

    # Invalid input
    result = schema.execute_sync(
        """
        query {
            positiveValue(value: -1)
        }
        """
    )

    assert result.errors is not None
    assert "greater_than" in result.errors[0].message


def test_root_model_with_validators():
    """Test RootModel with custom validators."""

    class UniqueStrings(RootModel[list[str]]):
        """A list that must contain unique strings."""

        @pydantic.field_validator("root")
        @classmethod
        def check_unique(cls, v: list[str]) -> list[str]:
            if len(v) != len(set(v)):
                raise ValueError("All items must be unique")
            return v

    @strawberry.type
    class Query:
        @strawberry.field
        def unique_items(self, items: list[str]) -> list[str]:
            validated = UniqueStrings.model_validate(items)
            return validated.root

    schema = strawberry.Schema(query=Query)

    # Valid input (unique items)
    result = schema.execute_sync(
        """
        query {
            uniqueItems(items: ["a", "b", "c"])
        }
        """
    )

    assert not result.errors
    assert result.data["uniqueItems"] == ["a", "b", "c"]

    # Invalid input (duplicate items)
    result = schema.execute_sync(
        """
        query {
            uniqueItems(items: ["a", "b", "a"])
        }
        """
    )

    assert result.errors is not None
    assert "unique" in result.errors[0].message.lower()


def test_root_model_in_output_type():
    """Test using RootModel in output type context."""

    class Scores(RootModel[list[int]]):
        """A list of scores."""

    @strawberry.pydantic.type
    class GameResult(pydantic.BaseModel):
        player_name: str
        scores: list[int]

    @strawberry.type
    class Query:
        @strawberry.field
        def game_result(self) -> GameResult:
            # Use RootModel to validate scores before creating result
            validated_scores = Scores.model_validate([85, 90, 78])
            return GameResult(player_name="Alice", scores=validated_scores.root)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            gameResult {
                playerName
                scores
            }
        }
        """
    )

    assert not result.errors
    assert result.data["gameResult"]["playerName"] == "Alice"
    assert result.data["gameResult"]["scores"] == [85, 90, 78]


def test_root_model_nested_validation():
    """Test RootModel with nested models in a resolver."""

    class InnerItem(pydantic.BaseModel):
        name: str
        quantity: int = Field(ge=1)

    class ItemList(RootModel[list[InnerItem]]):
        """A validated list of items."""

        @pydantic.field_validator("root")
        @classmethod
        def check_not_empty(cls, v: list[InnerItem]) -> list[InnerItem]:
            if not v:
                raise ValueError("Item list cannot be empty")
            return v

    @strawberry.pydantic.type
    class OrderSummary(pydantic.BaseModel):
        total_items: int
        item_names: list[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def process_items(
            self, names: list[str], quantities: list[int]
        ) -> OrderSummary:
            # Build list of items and validate with RootModel
            raw_items = [
                {"name": n, "quantity": q}
                for n, q in zip(names, quantities, strict=True)
            ]
            validated = ItemList.model_validate(raw_items)
            return OrderSummary(
                total_items=sum(item.quantity for item in validated.root),
                item_names=[item.name for item in validated.root],
            )

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            processItems(
                names: ["Widget", "Gadget"],
                quantities: [2, 3]
            ) {
                totalItems
                itemNames
            }
        }
        """
    )

    assert not result.errors
    assert result.data["processItems"]["totalItems"] == 5
    assert result.data["processItems"]["itemNames"] == ["Widget", "Gadget"]

    # Test validation failure (empty list)
    result = schema.execute_sync(
        """
        query {
            processItems(names: [], quantities: []) {
                totalItems
            }
        }
        """
    )

    assert result.errors is not None
    assert "empty" in result.errors[0].message.lower()
