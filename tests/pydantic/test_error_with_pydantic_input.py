"""Test Pydantic validation error handling with @strawberry.pydantic.input."""

from typing import Union

import pydantic
from inline_snapshot import snapshot

import strawberry
from strawberry.permission import BasePermission
from strawberry.pydantic import Error, PydanticValidationErrorHandler


def test_pydantic_input_validation_error_converted_to_error():
    """Test that ValidationError from @strawberry.pydantic.input is converted to Error."""

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)
        age: pydantic.conint(ge=0, le=120)

    @strawberry.type
    class CreateUserSuccess:
        id: int
        message: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(
            self, input: CreateUserInput
        ) -> Union[CreateUserSuccess, Error]:
            # If we get here, validation passed
            return CreateUserSuccess(
                id=1, message=f"User {input.name} created successfully"
            )

    @strawberry.type
    class Query:
        dummy: str = "dummy"

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    # Test successful creation
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "John", age: 30 }) {
                ... on CreateUserSuccess {
                    id
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
    assert result.data["createUser"]["id"] == 1
    assert result.data["createUser"]["message"] == "User John created successfully"

    # Test validation error - should be converted to Error type
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "J", age: -5 }) {
                ... on CreateUserSuccess {
                    id
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

    assert not result.errors  # No GraphQL errors
    assert result.data == snapshot(
        {
            "createUser": {
                "errors": [
                    {
                        "type": "string_too_short",
                        "loc": ["name"],
                        "msg": "String should have at least 2 characters",
                    },
                    {
                        "type": "greater_than_equal",
                        "loc": ["age"],
                        "msg": "Input should be greater than or equal to 0",
                    },
                ]
            }
        }
    )


def test_pydantic_input_validation_error_without_error_in_union():
    """Test that ValidationError is still raised if Error is not in the return type."""

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)
        age: pydantic.conint(ge=0)

    @strawberry.type
    class CreateUserSuccess:
        id: int
        message: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> CreateUserSuccess:
            # If we get here, validation passed
            return CreateUserSuccess(
                id=1, message=f"User {input.name} created successfully"
            )

    @strawberry.type
    class Query:
        dummy: str = "dummy"

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    # Test validation error - should raise GraphQL error
    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "J", age: -5 }) {
                id
                message
            }
        }
        """
    )

    assert result.errors
    assert len(result.errors) == 1
    assert "validation error" in result.errors[0].message.lower()


def test_graphql_schema_with_pydantic_input():
    """Test that the GraphQL schema is correct with Pydantic input."""

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.type
    class UserResult:
        success: bool
        message: str

    @strawberry.type
    class Query:
        dummy: str = "dummy"

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: UserInput) -> Union[UserResult, Error]:
            return UserResult(success=True, message="ok")

    schema = strawberry.Schema(query=Query, mutation=Mutation)

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

type Mutation {
  createUser(input: UserInput!): UserResultError!
}

type Query {
  dummy: String!
}

input UserInput {
  name: String!
  age: Int!
}

type UserResult {
  success: Boolean!
  message: String!
}

union UserResultError = UserResult | Error\
"""
    )


def test_pydantic_input_validation_error_is_mapped_before_permissions_run():
    # Argument conversion (where pydantic input validation runs) happens before
    # the field-extension chain, so a validation error is mapped to the union
    # result directly and the permission never runs. Mirrors the core
    # ``test_argument_conversion_error_is_mapped_before_permissions_run``.
    permission_ran = False

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    @strawberry.type
    class CreateUserSuccess:
        id: int

    class Deny(BasePermission):
        message = "denied"

        def has_permission(self, source, info, **kwargs):  # noqa: ANN003
            nonlocal permission_ran
            permission_ran = True
            return False

    @strawberry.type
    class Mutation:
        @strawberry.mutation(permission_classes=[Deny])
        def create_user(
            self, input: CreateUserInput
        ) -> Union[CreateUserSuccess, Error]:
            return CreateUserSuccess(id=1)

    @strawberry.type
    class Query:
        dummy: str = "dummy"

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            createUser(input: { name: "J" }) {
                ... on CreateUserSuccess {
                    id
                }
                ... on Error {
                    errors {
                        type
                    }
                }
            }
        }
        """
    )

    assert result.errors is None
    assert result.data == {"createUser": {"errors": [{"type": "string_too_short"}]}}
    assert permission_ran is False
