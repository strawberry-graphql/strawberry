from typing import Union

import strawberry
from strawberry.arguments import UNSET
from strawberry.validators import StrawberryErrorType


def validate_email(value, info):
    if "@" not in value:
        raise ErrorType(email="Invalid email")
    return value.strip()


def validate_postcode(value, info):
    postcode = int(value)
    if postcode < 1 or postcode > 99999:
        raise ErrorType(postcode="Invalid post code")
    return f"{postcode:05d}"


@strawberry.type
class SuccessType:
    message: str


@strawberry.type
class ErrorType(StrawberryErrorType):
    message: str = "Check input fields"
    email: str = UNSET
    postcode: str = UNSET


@strawberry.input
class InputType:
    email: str = strawberry.field(validators=[validate_email])
    postcode: str = strawberry.field(validators=[validate_postcode])


@strawberry.type
class Query:
    dummy: str


@strawberry.type
class Mutation:
    @strawberry.mutation
    def save_data(self, data: InputType) -> Union[SuccessType, ErrorType]:
        return SuccessType(message="Data saved")


schema = strawberry.Schema(query=Query, mutation=Mutation)
query = """
mutation($data: InputType!) {
    saveData(data: $data) {
        ... on SuccessType {
            message
        }
        ... on ErrorType {
            message
            email
            postcode
        }
    }
}
"""


def test_success():
    result = schema.execute_sync(
        query, variable_values={"data": {"email": "a@a.aa", "postcode": "1234"}}
    )
    assert not result.errors
    assert result.data["saveData"] == {
        "message": "Data saved",
    }


def test_error():
    result = schema.execute_sync(
        query, variable_values={"data": {"email": "asd", "postcode": "-1"}}
    )
    assert not result.errors == "Check input fields"
    assert result.data["saveData"] == {
        "message": "Check input fields",
        "email": "Invalid email",
        "postcode": "Invalid post code",
    }
