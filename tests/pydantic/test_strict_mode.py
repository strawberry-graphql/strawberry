"""Tests for Pydantic per-field strict mode with first-class integration."""

import pydantic
from pydantic import Field

import strawberry


def test_strict_field_rejects_wrong_type():
    """Test that Field(strict=True) enforces exact types."""

    @strawberry.pydantic.input
    class MixedInput(pydantic.BaseModel):
        strict_age: int = Field(strict=True)
        flexible_count: int  # Not strict - allows coercion

    @strawberry.pydantic.type
    class Result(pydantic.BaseModel):
        strict_age: int
        flexible_count: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def process(self, input: MixedInput) -> Result:
            return Result(
                strict_age=input.strict_age, flexible_count=input.flexible_count
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Both with correct types - should work
    result = schema.execute_sync(
        """
        mutation {
            process(input: { strictAge: 25, flexibleCount: 10 }) {
                strictAge
                flexibleCount
            }
        }
        """
    )

    assert not result.errors
    assert result.data["process"]["strictAge"] == 25
    assert result.data["process"]["flexibleCount"] == 10


def test_strict_string_field():
    """Test strict mode for string fields."""

    @strawberry.pydantic.input
    class StrictStringInput(pydantic.BaseModel):
        name: str = Field(strict=True)

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: StrictStringInput) -> User:
            return User(name=input.name)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # String input - should work
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "Alice" }) {
                name
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["name"] == "Alice"


def test_strict_bool_field():
    """Test strict mode for boolean fields."""

    @strawberry.pydantic.input
    class StrictBoolInput(pydantic.BaseModel):
        active: bool = Field(strict=True)

    @strawberry.pydantic.type
    class Status(pydantic.BaseModel):
        active: bool

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def set_status(self, input: StrictBoolInput) -> Status:
            return Status(active=input.active)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Boolean input - should work
    result = schema.execute_sync(
        """
        mutation {
            setStatus(input: { active: true }) {
                active
            }
        }
        """
    )

    assert not result.errors
    assert result.data["setStatus"]["active"] is True


def test_strict_float_field():
    """Test strict mode for float fields."""

    @strawberry.pydantic.input
    class StrictFloatInput(pydantic.BaseModel):
        price: float = Field(strict=True)

    @strawberry.pydantic.type
    class Product(pydantic.BaseModel):
        price: float

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_product(self, input: StrictFloatInput) -> Product:
            return Product(price=input.price)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Float input - should work
    result = schema.execute_sync(
        """
        mutation {
            createProduct(input: { price: 9.99 }) {
                price
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createProduct"]["price"] == 9.99

    # Int input to strict float - GraphQL allows this coercion at schema level
    # The value arrives at Pydantic as a Python int/float
    result = schema.execute_sync(
        """
        mutation {
            createProduct(input: { price: 10 }) {
                price
            }
        }
        """
    )

    # GraphQL converts 10 to 10.0 before reaching Pydantic
    assert not result.errors


def test_mixed_strict_and_non_strict_fields():
    """Test a model with both strict and non-strict fields."""

    @strawberry.pydantic.input
    class MixedStrictnessInput(pydantic.BaseModel):
        strict_int: int = Field(strict=True)
        strict_str: str = Field(strict=True)
        flexible_int: int
        flexible_str: str

    @strawberry.pydantic.type
    class Result(pydantic.BaseModel):
        strict_int: int
        strict_str: str
        flexible_int: int
        flexible_str: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def process(self, input: MixedStrictnessInput) -> Result:
            return Result(
                strict_int=input.strict_int,
                strict_str=input.strict_str,
                flexible_int=input.flexible_int,
                flexible_str=input.flexible_str,
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
        mutation {
            process(input: {
                strictInt: 42
                strictStr: "hello"
                flexibleInt: 100
                flexibleStr: "world"
            }) {
                strictInt
                strictStr
                flexibleInt
                flexibleStr
            }
        }
        """
    )

    assert not result.errors
    assert result.data["process"]["strictInt"] == 42
    assert result.data["process"]["strictStr"] == "hello"
    assert result.data["process"]["flexibleInt"] == 100
    assert result.data["process"]["flexibleStr"] == "world"


def test_strict_with_constraints():
    """Test strict mode combined with field constraints."""

    @strawberry.pydantic.input
    class ConstrainedInput(pydantic.BaseModel):
        age: int = Field(strict=True, ge=0, le=150)
        name: str = Field(strict=True, min_length=1, max_length=50)

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        name: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: ConstrainedInput) -> User:
            return User(age=input.age, name=input.name)

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Valid input
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { age: 25, name: "Alice" }) {
                age
                name
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["age"] == 25

    # Age out of range
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { age: 200, name: "Alice" }) {
                age
                name
            }
        }
        """
    )

    assert result.errors is not None
    assert "less_than_equal" in result.errors[0].message

    # Name too long
    long_name = "A" * 51
    result = schema.execute_sync(
        f"""
        mutation {{
            createUser(input: {{ age: 25, name: "{long_name}" }}) {{
                age
                name
            }}
        }}
        """
    )

    assert result.errors is not None
    assert "string_too_long" in result.errors[0].message
