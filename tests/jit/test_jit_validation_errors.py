"""Comprehensive validation error tests for JIT compiler.

Tests input validation, type mismatches, required fields, and enum validation.
"""

from enum import Enum

import pytest

import strawberry
from strawberry.jit import compile_query


@strawberry.enum
class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


@strawberry.input
class UserInput:
    name: str
    email: str
    age: int | None = None


@strawberry.input
class CreatePostInput:
    title: str
    content: str
    status: Status
    author: UserInput


@strawberry.type
class User:
    name: str
    email: str
    age: int | None


@strawberry.type
class Post:
    title: str
    content: str
    status: Status


@strawberry.type
class Query:
    @strawberry.field
    def user(self, name: str, email: str, age: int | None = None) -> User:
        """Query requiring specific arguments."""
        return User(name=name, email=email, age=age)

    @strawberry.field
    def create_post(self, input: CreatePostInput) -> Post:
        """Mutation with complex input type."""
        return Post(
            title=input.title,
            content=input.content,
            status=input.author.name,  # Intentionally wrong for testing
        )

    @strawberry.field
    def get_status(self, status: Status) -> Status:
        """Query with enum argument."""
        return status

    @strawberry.field
    def required_field(self, value: str) -> str:
        """Query with required field."""
        return f"Value: {value}"

    @strawberry.field
    def typed_list(self, ids: list[int]) -> list[int]:
        """Query with typed list."""
        return ids


def test_missing_required_argument():
    """Test validation error when required argument is missing."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        user(name: "John") {
            name
            email
        }
    }
    """

    with pytest.raises(ValueError, match="validation failed"):
        compile_query(schema, query)


def test_type_mismatch_string_to_int():
    """Test validation error for type mismatch."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        user(name: "John", email: "john@example.com", age: "not a number") {
            name
        }
    }
    """

    with pytest.raises(ValueError, match="validation failed"):
        compile_query(schema, query)


def test_invalid_enum_value():
    """Test validation error for invalid enum value."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        getStatus(status: INVALID)
    }
    """

    with pytest.raises(ValueError, match="validation failed"):
        compile_query(schema, query)


def test_valid_enum_value():
    """Test that valid enum values work correctly."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        getStatus(status: ACTIVE)
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["getStatus"] == "ACTIVE"


def test_missing_required_input_field():
    """Test validation error when required input field is missing."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        createPost(input: {
            title: "Test Post"
            status: ACTIVE
            author: {
                name: "John"
                email: "john@example.com"
            }
        }) {
            title
        }
    }
    """

    # Missing 'content' field
    with pytest.raises(ValueError, match="validation failed"):
        compile_query(schema, query)


def test_type_mismatch_in_list():
    """Test validation error for type mismatch in list."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        typedList(ids: [1, 2, "three", 4])
    }
    """

    with pytest.raises(ValueError, match="validation failed"):
        compile_query(schema, query)


def test_valid_input_object():
    """Test that valid input objects work correctly."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        createPost(input: {
            title: "Test Post"
            content: "This is content"
            status: ACTIVE
            author: {
                name: "John"
                email: "john@example.com"
            }
        }) {
            title
            content
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["createPost"]["title"] == "Test Post"
    assert result["data"]["createPost"]["content"] == "This is content"


def test_optional_field_omitted():
    """Test that optional fields can be omitted."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        user(name: "John", email: "john@example.com") {
            name
            email
            age
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["user"]["name"] == "John"
    assert result["data"]["user"]["email"] == "john@example.com"
    assert result["data"]["user"]["age"] is None


def test_optional_field_provided():
    """Test that optional fields can be provided."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        user(name: "John", email: "john@example.com", age: 30) {
            name
            age
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["user"]["name"] == "John"
    assert result["data"]["user"]["age"] == 30


def test_validation_with_variables_missing_required():
    """Test validation error with variables when required variable is missing."""
    schema = strawberry.Schema(Query)
    query = """
    query GetUser($name: String!, $email: String!) {
        user(name: $name, email: $email) {
            name
            email
        }
    }
    """

    compiled = compile_query(schema, query)

    # Missing required variable 'email'
    result = compiled(Query(), variables={"name": "John"})

    # Should have validation error
    assert "errors" in result
    assert len(result["errors"]) > 0


def test_validation_with_variables_type_mismatch():
    """Test that variables with wrong type cause runtime validation errors."""
    schema = strawberry.Schema(Query)
    query = """
    query GetUser($name: String!, $email: String!, $age: Int) {
        user(name: $name, email: $email, age: $age) {
            name
            age
        }
    }
    """

    compiled = compile_query(schema, query)

    # Provide string for int variable
    result = compiled(
        Query(),
        variables={"name": "John", "email": "john@example.com", "age": "thirty"},
    )

    # Should have validation error
    assert "errors" in result
    assert len(result["errors"]) > 0


def test_validation_with_valid_variables():
    """Test that valid variables work correctly."""
    schema = strawberry.Schema(Query)
    query = """
    query GetUser($name: String!, $email: String!, $age: Int) {
        user(name: $name, email: $email, age: $age) {
            name
            email
            age
        }
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(
        Query(), variables={"name": "John", "email": "john@example.com", "age": 30}
    )

    assert result["data"]["user"]["name"] == "John"
    assert result["data"]["user"]["email"] == "john@example.com"
    assert result["data"]["user"]["age"] == 30


def test_unknown_field():
    """Test validation error for unknown field."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        user(name: "John", email: "john@example.com") {
            name
            unknownField
        }
    }
    """

    with pytest.raises(ValueError, match="validation failed"):
        compile_query(schema, query)


def test_wrong_argument_name():
    """Test validation error for wrong argument name."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        user(fullName: "John", email: "john@example.com") {
            name
        }
    }
    """

    with pytest.raises(ValueError, match="validation failed"):
        compile_query(schema, query)


def test_null_for_non_nullable():
    """Test validation error when providing null for non-nullable field."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        requiredField(value: null)
    }
    """

    with pytest.raises(ValueError, match="validation failed"):
        compile_query(schema, query)


def test_complex_input_validation():
    """Test validation of complex nested input objects."""
    schema = strawberry.Schema(Query)

    # Valid query
    valid_query = """
    query {
        createPost(input: {
            title: "Test"
            content: "Content"
            status: ACTIVE
            author: {
                name: "John"
                email: "john@example.com"
                age: 30
            }
        }) {
            title
        }
    }
    """

    compiled = compile_query(schema, valid_query)
    result = compiled(Query())
    assert "data" in result
    assert result["data"]["createPost"]["title"] == "Test"


def test_empty_list_valid():
    """Test that empty list is valid."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        typedList(ids: [])
    }
    """

    compiled = compile_query(schema, query)
    result = compiled(Query())

    assert result["data"]["typedList"] == []


def test_validation_error_message_quality():
    """Test that validation errors have helpful messages."""
    schema = strawberry.Schema(Query)
    query = """
    query {
        user(name: "John") {
            name
        }
    }
    """

    try:
        compile_query(schema, query)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        error_message = str(e)
        # Should mention validation failure
        assert "validation" in error_message.lower()
        # Should be informative
        assert len(error_message) > 20
