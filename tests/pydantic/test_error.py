"""Tests for the generic Pydantic Error type."""

from typing import Union

from inline_snapshot import snapshot

import pydantic
import strawberry
from strawberry.pydantic import Error


def test_error_type_from_validation_error():
    """Test creating Error from ValidationError."""

    class UserInput(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)
        age: pydantic.conint(ge=0)

    # Test with multiple validation errors
    try:
        UserInput(name="A", age=-5)
    except pydantic.ValidationError as e:
        error = Error.from_validation_error(e)

        assert len(error.errors) == 2

        # Check first error (name)
        assert error.errors[0].type == "string_too_short"
        assert error.errors[0].loc == ["name"]
        assert "at least 2 characters" in error.errors[0].msg

        # Check second error (age)
        assert error.errors[1].type == "greater_than_equal"
        assert error.errors[1].loc == ["age"]
        assert "greater than or equal to 0" in error.errors[1].msg


def test_error_type_with_nested_fields():
    """Test Error type with nested field validation errors."""

    class AddressInput(pydantic.BaseModel):
        street: pydantic.constr(min_length=5)
        city: str
        zip_code: pydantic.constr(pattern=r"^\d{5}$")

    class UserInput(pydantic.BaseModel):
        name: str
        address: AddressInput

    try:
        UserInput(
            name="John",
            address={"street": "Oak", "city": "NYC", "zip_code": "ABC"},
        )
    except pydantic.ValidationError as e:
        error = Error.from_validation_error(e)

        assert len(error.errors) == 2

        # Check nested street error
        assert error.errors[0].type == "string_too_short"
        assert error.errors[0].loc == ["address", "street"]
        assert "at least 5 characters" in error.errors[0].msg

        # Check nested zip_code error
        assert error.errors[1].type == "string_pattern_mismatch"
        assert error.errors[1].loc == ["address", "zip_code"]


def test_error_in_mutation_with_union_return():
    """Test using Error in a mutation with union return type."""

    # Use a regular strawberry input type to allow passing invalid data
    @strawberry.input
    class CreateUserInput:
        name: str
        age: int

    # Define the Pydantic model for validation
    class CreateUserModel(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)
        age: pydantic.conint(ge=0, le=120)

    @strawberry.type
    class CreateUserSuccess:
        user_id: int
        message: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(
            self, input: CreateUserInput
        ) -> Union[CreateUserSuccess, Error]:
            try:
                # Validate the input using Pydantic
                validated = CreateUserModel(name=input.name, age=input.age)
                # Simulate successful creation
                return CreateUserSuccess(
                    user_id=1, message=f"User {validated.name} created successfully"
                )
            except pydantic.ValidationError as e:
                return Error.from_validation_error(e)

    @strawberry.type
    class Query:
        dummy: str = "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test successful creation
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "John", age: 30 }) {
                ... on CreateUserSuccess {
                    userId
                    message
                }
                ... on Error {
                    errors {
                        type
                        loc
                        msg
                    }
                }
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createUser"]["userId"] == 1
    assert result.data["createUser"]["message"] == "User John created successfully"

    # Test validation error
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "J", age: -5 }) {
                ... on CreateUserSuccess {
                    userId
                    message
                }
                ... on Error {
                    errors {
                        type
                        loc
                        msg
                    }
                }
            }
        }
        """
    )

    assert not result.errors
    assert len(result.data["createUser"]["errors"]) == 2

    # Check first error
    assert result.data["createUser"]["errors"][0]["type"] == "string_too_short"
    assert result.data["createUser"]["errors"][0]["loc"] == ["name"]
    assert "at least 2 characters" in result.data["createUser"]["errors"][0]["msg"]

    # Check second error
    assert result.data["createUser"]["errors"][1]["type"] == "greater_than_equal"
    assert result.data["createUser"]["errors"][1]["loc"] == ["age"]


def test_error_graphql_schema():
    """Test that Error generates correct GraphQL schema."""

    @strawberry.type
    class Query:
        @strawberry.field
        def test_error(self) -> Error:
            # Dummy resolver
            return Error(errors=[])

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot(
        """\
type Error {
  errors: [ErrorDetail!]!
}

type ErrorDetail {
  type: String!
  loc: [String!]!
  msg: String!
}

type Query {
  testError: Error!
}"""
    )


def test_error_with_single_validation_error():
    """Test Error type with a single validation error."""

    class EmailInput(pydantic.BaseModel):
        email: pydantic.EmailStr

    try:
        EmailInput(email="not-an-email")
    except pydantic.ValidationError as e:
        error = Error.from_validation_error(e)

        assert len(error.errors) == 1
        assert error.errors[0].type in [
            "value_error",
            "email",
        ]  # Depends on Pydantic version
        assert error.errors[0].loc == ["email"]
        assert "email" in error.errors[0].msg.lower()


def test_error_with_list_field_validation():
    """Test Error type with validation errors in list fields."""

    class TagsInput(pydantic.BaseModel):
        tags: list[pydantic.constr(min_length=2)]

    try:
        TagsInput(tags=["ok", "a", "good", "b"])
    except pydantic.ValidationError as e:
        error = Error.from_validation_error(e)

        assert len(error.errors) == 2

        # Check errors for short tags
        assert error.errors[0].type == "string_too_short"
        assert error.errors[0].loc == ["tags", "1"]  # Index 1 is "a"

        assert error.errors[1].type == "string_too_short"
        assert error.errors[1].loc == ["tags", "3"]  # Index 3 is "b"
