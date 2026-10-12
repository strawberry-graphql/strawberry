import logging
from typing import Annotated

import pydantic
import pytest
from inline_snapshot import snapshot
from pydantic_core import PydanticCustomError

import strawberry
from strawberry.exceptions import StrawberryInputCoercionError
from strawberry.permission import BasePermission
from strawberry.pydantic import (
    InputValidationError,
    PydanticValidationErrorHandler,
    ValidationError,
    ValidationErrorDetail,
)


@strawberry.pydantic.input
class AddressInput(pydantic.BaseModel):
    zip_code: str = pydantic.Field(pattern=r"^\d{5}$")


@strawberry.pydantic.input
class SignUpInput(pydantic.BaseModel):
    password: str = pydantic.Field(min_length=12)
    address: AddressInput | None = None

    @pydantic.model_validator(mode="after")
    def check_password(self) -> "SignUpInput":
        if self.password == "password1234":
            raise ValueError("password is too common")

        return self


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    hello: str = "world"


ERRORS_QUERY = """
    mutation SignUp($input: SignUpInput!) {
        signUp(input: $input) {
            ... on User { name }
            ... on ValidationError { errors { location message type } }
        }
    }
"""


def _sign_up_schema() -> strawberry.Schema:
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def sign_up(self, input: SignUpInput) -> User | ValidationError:
            return User(name="Ada")

    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )


def test_schema():
    schema = _sign_up_schema()

    assert str(schema) == snapshot('''\
input AddressInput {
  zipCode: String!
}

type Mutation {
  signUp(input: SignUpInput!): UserValidationError!
}

type Query {
  hello: String!
}

input SignUpInput {
  password: String!
  address: AddressInput
}

type User {
  name: String!
}

union UserValidationError = User | ValidationError

"""The inputs failed validation."""
type ValidationError {
  """The problems with the input values."""
  errors: [ValidationErrorDetail!]!
}

"""A problem with an input value."""
type ValidationErrorDetail {
  """The argument, then field names and list indexes, all as strings."""
  location: [String!]!

  """The reason the value is invalid."""
  message: String!

  """The Pydantic error type, like `string_too_short`."""
  type: String!
}\
''')


def test_valid_input():
    result = _sign_up_schema().execute_sync(
        ERRORS_QUERY, variable_values={"input": {"password": "a long password"}}
    )

    assert not result.errors
    assert result.data == {"signUp": {"name": "Ada"}}


def test_invalid_input_is_returned_as_a_validation_error():
    result = _sign_up_schema().execute_sync(
        ERRORS_QUERY,
        variable_values={"input": {"password": "short", "address": {"zipCode": "x"}}},
    )

    assert not result.errors
    assert result.data == snapshot(
        {
            "signUp": {
                "errors": [
                    {
                        "location": ["input", "password"],
                        "message": "String should have at least 12 characters",
                        "type": "string_too_short",
                    },
                    {
                        "location": ["input", "address", "zipCode"],
                        "message": "String should match pattern '^\\d{5}$'",
                        "type": "string_pattern_mismatch",
                    },
                ]
            }
        }
    )


def test_model_errors_are_located_at_the_input():
    result = _sign_up_schema().execute_sync(
        ERRORS_QUERY, variable_values={"input": {"password": "password1234"}}
    )

    assert not result.errors
    assert result.data == {
        "signUp": {
            "errors": [
                {
                    "location": ["input"],
                    "message": "password is too common",
                    "type": "value_error",
                }
            ]
        }
    }


async def test_invalid_input_is_returned_as_a_validation_error_async():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def sign_up(self, input: SignUpInput) -> User | ValidationError:
            return User(name="Ada")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    result = await schema.execute(
        ERRORS_QUERY, variable_values={"input": {"password": "short"}}
    )

    assert not result.errors
    assert result.data == {
        "signUp": {
            "errors": [
                {
                    "location": ["input", "password"],
                    "message": "String should have at least 12 characters",
                    "type": "string_too_short",
                }
            ]
        }
    }


def test_invalid_input_without_a_validation_error_in_the_return_type():
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def sign_up(self, input: SignUpInput) -> User:
            return User(name="Ada")

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        'mutation { signUp(input: {password: "hunter2"}) { name } }'
    )

    assert result.data is None
    assert result.errors

    [error] = result.errors

    assert error.message == (
        "Invalid input: input.password: String should have at least 12 characters"
    )
    assert error.extensions == {
        "validationErrors": [
            {
                "location": ["input", "password"],
                "message": "String should have at least 12 characters",
                "type": "string_too_short",
            }
        ]
    }
    # the submitted value isn't sent back
    assert "hunter2" not in str(result.errors)
    # it's an input error, so that it can be told apart from server errors
    assert isinstance(error.original_error, InputValidationError)
    assert isinstance(error.original_error, StrawberryInputCoercionError)


def test_validation_errors_raised_by_resolvers_are_not_converted():
    class Row(pydantic.BaseModel):
        age: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def load(self) -> User | ValidationError:
            # e.g. a bug in server code, not invalid input
            Row(age="not a number")  # type: ignore[arg-type]

            return User(name="Ada")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    result = schema.execute_sync("mutation { load { __typename } }")

    assert result.data is None
    assert result.errors
    assert isinstance(result.errors[0].original_error, pydantic.ValidationError)


def test_locations_go_through_lists_and_strawberry_inputs():
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int = pydantic.Field(gt=0)

    @strawberry.input
    class OrderInput:
        items: list[ItemInput]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_orders(self, orders: list[OrderInput]) -> User | ValidationError:
            return User(name="Ada")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            createOrders(orders: [{items: []}, {items: [{quantity: 1}, {quantity: 0}]}]) {
                ... on ValidationError { errors { location } }
            }
        }
        """
    )

    assert not result.errors
    assert result.data == {
        "createOrders": {
            "errors": [{"location": ["orders", "1", "items", "1", "quantity"]}]
        }
    }


def test_locations_use_graphql_names():
    @strawberry.pydantic.input
    class ProfileInput(pydantic.BaseModel):
        display_name: str = pydantic.Field(min_length=1)
        bio: Annotated[str, strawberry.field(name="about")] = pydantic.Field(
            max_length=3
        )
        website: str = pydantic.Field(alias="homepage", pattern="^https://")

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update_profile(self, profile_data: ProfileInput) -> User | ValidationError:
            return User(name="Ada")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            updateProfile(profileData: {displayName: "", about: "long", website: "x"}) {
                ... on ValidationError { errors { location } }
            }
        }
        """
    )

    assert not result.errors
    assert result.data == {
        "updateProfile": {
            "errors": [
                {"location": ["profileData", "displayName"]},
                {"location": ["profileData", "about"]},
                {"location": ["profileData", "website"]},
            ]
        }
    }


def test_validation_errors_are_returned_before_permissions_run():
    # pydantic inputs are validated when the arguments are converted, before the
    # field extensions, so the permission never runs. Mirrors the core
    # `test_argument_conversion_error_is_mapped_before_permissions_run`.
    permission_ran = False

    class Deny(BasePermission):
        message = "denied"

        def has_permission(self, source, info, **kwargs) -> bool:  # noqa: ANN003
            nonlocal permission_ran
            permission_ran = True

            return False

    @strawberry.type
    class Mutation:
        @strawberry.mutation(permission_classes=[Deny])
        def sign_up(self, input: SignUpInput) -> User | ValidationError:
            return User(name="Ada")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    result = schema.execute_sync(
        ERRORS_QUERY, variable_values={"input": {"password": "short"}}
    )

    assert not result.errors
    assert result.data["signUp"]["errors"][0]["type"] == "string_too_short"
    assert permission_ran is False


def test_pydantic_input_payload_is_not_logged(caplog: pytest.LogCaptureFixture):
    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def sign_up(self, input: SignUpInput) -> User:
            return User(name="Ada")

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    with caplog.at_level(logging.ERROR):
        result = schema.execute_sync(
            "mutation SignUp($input: SignUpInput!) { signUp(input: $input) { name } }",
            variable_values={"input": {"password": "hunter2"}},
        )

    assert result.errors
    assert "Invalid input" in caplog.text
    assert "hunter2" not in caplog.text
    error = result.errors[0].original_error
    assert isinstance(error, InputValidationError)
    assert error.__cause__ is None
    assert error.__context__ is None


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (
            ValueError("Rejected value: 'original value'"),
            "Rejected value: 'original value'",
        ),
        (ValueError("Value error, intentional"), "Value error, intentional"),
        (
            PydanticCustomError("value_error", "Value error, custom"),
            "Value error, custom",
        ),
    ],
)
def test_validator_messages_are_preserved_verbatim_as_data(error, message):
    @strawberry.pydantic.input
    class MessageInput(pydantic.BaseModel):
        text: str

        @pydantic.field_validator("text")
        @classmethod
        def reject(cls, value: str) -> str:
            raise error

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def submit(self, input: MessageInput) -> User | ValidationError:
            return User(name="Ada")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )
    result = schema.execute_sync(
        'mutation { submit(input: {text: "original value"}) { '
        "... on ValidationError { errors { location message type } } } }"
    )

    # Input payloads are excluded, but messages are not redacted, even when
    # a validator deliberately includes the submitted value in its message.
    assert not result.errors
    assert result.data == {
        "submit": {
            "errors": [
                {
                    "location": ["input", "text"],
                    "message": message,
                    "type": "value_error",
                }
            ]
        }
    }


def test_locations_of_renamed_fields():
    @strawberry.pydantic.input
    class ProfileInput(pydantic.BaseModel):
        # the GraphQL name of a field can be the python name of another one
        legacy_name: Annotated[str, strawberry.field(name="name")] = ""
        name: Annotated[str, strawberry.field(name="displayName")] = pydantic.Field(
            min_length=3
        )
        nickname: Annotated[str | None, strawberry.field(name="handle")] = (
            pydantic.Field(alias="nick", min_length=3)
        )

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update(self, data: ProfileInput) -> User | ValidationError:
            return User(name="Ada")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            update(data: {name: "a fine legacy name", displayName: "x", handle: "y"}) {
                ... on ValidationError { errors { location type } }
            }
        }
        """
    )

    assert not result.errors
    assert result.data == {
        "update": {
            "errors": [
                {"location": ["data", "displayName"], "type": "string_too_short"},
                {"location": ["data", "handle"], "type": "string_too_short"},
            ]
        }
    }


def test_locations_end_at_values_that_are_not_part_of_the_schema():
    @strawberry.pydantic.input
    class TransferInput(pydantic.BaseModel):
        amount: int
        risk_score: strawberry.Private[int] = 0

        @pydantic.model_validator(mode="before")
        @classmethod
        def score(cls, data: dict) -> dict:
            return {**data, "risk_score": "unknown"}

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def transfer(self, transfer: TransferInput) -> User | ValidationError:
            return User(name="Ada")

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        exception_handlers=[PydanticValidationErrorHandler()],
    )

    result = schema.execute_sync(
        """
        mutation {
            transfer(transfer: {amount: 1}) {
                ... on ValidationError { errors { location type } }
            }
        }
        """
    )

    assert not result.errors
    assert result.data == {
        "transfer": {"errors": [{"location": ["transfer"], "type": "int_parsing"}]}
    }


def test_error_message():
    def detail(location: list[str]) -> ValidationErrorDetail:
        return ValidationErrorDetail(
            location=location, message="Invalid", type="invalid"
        )

    assert InputValidationError([detail(["input", "name"]), detail([])]).message == (
        "Invalid input: input.name: Invalid; Invalid"
    )

    # the errors are all in the extensions
    error = InputValidationError([detail(["input", str(index)]) for index in range(7)])

    assert error.message == (
        "Invalid input: input.0: Invalid; input.1: Invalid; input.2: Invalid; "
        "input.3: Invalid; input.4: Invalid (and 2 more)"
    )
    assert len(error.extensions["validationErrors"]) == 7
    assert len(error.errors) == 7
    assert error.errors[6].location == ["input", "6"]
