"""Tests for Pydantic v2 TypeAdapter with Strawberry.

TypeAdapter allows validation of arbitrary types without creating a full BaseModel.
This is useful for validating scalars, lists, and other types in resolvers.
"""

from typing import Annotated

import pydantic
from pydantic import Field, TypeAdapter, ValidationError

import strawberry


def test_type_adapter_for_scalar_validation():
    """Test using TypeAdapter to validate scalar values in a resolver."""

    # Create a type adapter for validating positive integers
    PositiveInt = Annotated[int, Field(gt=0)]
    positive_int_adapter = TypeAdapter(PositiveInt)

    @strawberry.type
    class Query:
        @strawberry.field
        def validate_positive(self, value: int) -> int:
            # Use TypeAdapter to validate the input
            return positive_int_adapter.validate_python(value)

    schema = strawberry.Schema(query=Query)

    # Valid input
    result = schema.execute_sync(
        """
        query {
            validatePositive(value: 42)
        }
        """
    )

    assert not result.errors
    assert result.data["validatePositive"] == 42

    # Invalid input (negative)
    result = schema.execute_sync(
        """
        query {
            validatePositive(value: -1)
        }
        """
    )

    assert result.errors is not None
    assert "greater_than" in result.errors[0].message


def test_type_adapter_for_string_validation():
    """Test using TypeAdapter for string validation."""

    # Create a type adapter for validating email-like strings
    EmailStr = Annotated[str, Field(min_length=3, pattern=r".*@.*\..*")]
    email_adapter = TypeAdapter(EmailStr)

    @strawberry.type
    class Query:
        @strawberry.field
        def validate_email(self, email: str) -> str:
            return email_adapter.validate_python(email)

    schema = strawberry.Schema(query=Query)

    # Valid email
    result = schema.execute_sync(
        """
        query {
            validateEmail(email: "test@example.com")
        }
        """
    )

    assert not result.errors
    assert result.data["validateEmail"] == "test@example.com"

    # Invalid email
    result = schema.execute_sync(
        """
        query {
            validateEmail(email: "notanemail")
        }
        """
    )

    assert result.errors is not None
    assert "string_pattern_mismatch" in result.errors[0].message


def test_type_adapter_for_list_validation():
    """Test using TypeAdapter to validate list contents."""

    # Create a type adapter for validating a list of positive integers
    PositiveIntList = list[Annotated[int, Field(ge=0)]]
    list_adapter = TypeAdapter(PositiveIntList)

    @strawberry.type
    class Query:
        @strawberry.field
        def validate_numbers(self, numbers: list[int]) -> list[int]:
            return list_adapter.validate_python(numbers)

    schema = strawberry.Schema(query=Query)

    # Valid input
    result = schema.execute_sync(
        """
        query {
            validateNumbers(numbers: [1, 2, 3])
        }
        """
    )

    assert not result.errors
    assert result.data["validateNumbers"] == [1, 2, 3]

    # Invalid input (contains negative)
    result = schema.execute_sync(
        """
        query {
            validateNumbers(numbers: [1, -2, 3])
        }
        """
    )

    assert result.errors is not None
    assert "greater_than_equal" in result.errors[0].message


def test_type_adapter_with_complex_type():
    """Test TypeAdapter with a more complex nested type."""

    from typing import TypedDict

    class UserData(TypedDict):
        name: str
        age: int

    user_adapter = TypeAdapter(UserData)

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.type
    class Query:
        @strawberry.field
        def validate_user(self, input: UserInput) -> str:
            # Convert to dict and validate with TypeAdapter
            user_data = {"name": input.name, "age": input.age}
            validated = user_adapter.validate_python(user_data)
            return f"{validated['name']} is {validated['age']} years old"

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            validateUser(input: { name: "Alice", age: 30 })
        }
        """
    )

    assert not result.errors
    assert result.data["validateUser"] == "Alice is 30 years old"


def test_type_adapter_validation_error_handling():
    """Test that TypeAdapter validation errors are properly handled."""

    BoundedInt = Annotated[int, Field(ge=0, le=100)]
    adapter = TypeAdapter(BoundedInt)

    @strawberry.type
    class Query:
        @strawberry.field
        def bounded_value(self, value: int) -> int:
            try:
                return adapter.validate_python(value)
            except ValidationError as e:
                # Re-raise as a more user-friendly error
                raise ValueError(f"Invalid value: {e.errors()[0]['msg']}") from None

    schema = strawberry.Schema(query=Query)

    # Value too high
    result = schema.execute_sync(
        """
        query {
            boundedValue(value: 150)
        }
        """
    )

    assert result.errors is not None
    assert "Invalid value" in result.errors[0].message


def test_type_adapter_with_coercion():
    """Test that TypeAdapter coercion works as expected."""

    # TypeAdapter can coerce string to int if strict=False (default)
    adapter = TypeAdapter(int)

    # In resolvers, we can use this for flexible input handling
    @strawberry.type
    class Query:
        @strawberry.field
        def coerce_to_int(self, value: str) -> int:
            # This would coerce "42" to 42
            return adapter.validate_python(value)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            coerceToInt(value: "42")
        }
        """
    )

    assert not result.errors
    assert result.data["coerceToInt"] == 42


def test_type_adapter_strict_mode():
    """Test TypeAdapter with strict mode."""

    adapter = TypeAdapter(int)

    @strawberry.type
    class Query:
        @strawberry.field
        def strict_int(self, value: str) -> int:
            # Strict mode will reject string input
            return adapter.validate_python(value, strict=True)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            strictInt(value: "42")
        }
        """
    )

    assert result.errors is not None
    # Strict mode rejects string input for int
    assert "int_type" in result.errors[0].message or "type" in result.errors[0].message
