from typing import Dict, List, Union

import pydantic
import pytest

import strawberry
from strawberry.experimental.pydantic._compat import IS_PYDANTIC_V2
from strawberry.experimental.pydantic.pydantic_first_class import first_class


def test_mutation():
    @first_class(is_input=True)
    class CreateUserInput(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    @first_class()
    class UserType(pydantic.BaseModel):
        name: str

    @strawberry.type
    class Query:
        h: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> UserType:
            return UserType(name=input.name)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
        mutation {
            createUser(input: { name: "Patrick" }) {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["createUser"]["name"] == "Patrick"


def test_mutation_with_validation():
    @first_class(is_input=True)
    class CreateUserInput(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    @first_class()
    class UserType(pydantic.BaseModel):
        name: str

    @strawberry.type
    class Query:
        h: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> UserType:
            return UserType(name=input.name)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
        mutation {
            createUser(input: { name: "P" }) {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    if IS_PYDANTIC_V2:
        assert result.errors[0].message == (
            "1 validation error for CreateUserInput\n"
            "name\n"
            "  String should have at least 2 characters [type=string_too_short, "
            "input_value='P', input_type=str]\n"
            "    For further information visit "
            "https://errors.pydantic.dev/2.0.3/v/string_too_short"
        )
    else:
        assert result.errors[0].message == (
            "1 validation error for CreateUserInput\nname\n  ensure this value has at "
            "least 2 characters (type=value_error.any_str.min_length; limit_value=2)"
        )


def test_mutation_with_validation_of_nested_model():
    @first_class(is_input=True)
    class HobbyInput(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    @first_class(is_input=True)
    class CreateUserInput(pydantic.BaseModel):
        hobby: HobbyInput

    class UserModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(UserModel)
    class UserType:
        name: strawberry.auto

    @strawberry.type
    class Query:
        h: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> UserType:
            return UserType(name=input.hobby.name)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
        mutation {
            createUser(input: { hobby: { name: "P" } }) {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    if IS_PYDANTIC_V2:
        assert result.errors[0].message == (
            "1 validation error for HobbyInput\n"
            "name\n"
            "  String should have at least 2 characters [type=string_too_short, "
            "input_value='P', input_type=str]\n"
            "    For further information visit "
            "https://errors.pydantic.dev/2.0.3/v/string_too_short"
        )

    else:
        assert result.errors[0].message == (
            "1 validation error for HobbyInput\nname\n"
            "  ensure this value has at least 2 characters "
            "(type=value_error.any_str.min_length; limit_value=2)"
        )


@pytest.mark.xfail(
    reason="""No way to manually handle errors
the validation goes boom in convert_argument, not in the create_user resolver"""
)
def test_mutation_with_validation_and_error_type():
    @first_class(is_input=True)
    class CreateUserInput(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    @first_class()
    class UserType(pydantic.BaseModel):
        name: str

    @first_class()
    class UserError(pydantic.BaseModel):
        name: str

    @strawberry.type
    class Query:
        h: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> Union[UserType, UserError]:
            try:
                data = input
            except pydantic.ValidationError as e:
                # issue: the error will never be thrown here because the validation
                # happens in convert_argument
                args: Dict[str, List[str]] = {}
                for error in e.errors():
                    field = error["loc"][0]  # currently doesn't support nested errors
                    field_errors = args.get(field, [])
                    field_errors.append(error["msg"])
                    args[field] = field_errors
                return UserError(**args)
            else:
                return UserType(name=data.name)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
        mutation {
            createUser(input: { name: "P" }) {
                ... on UserType {
                    name
                }
                ... on UserError {
                    nameErrors: name
                }
            }
        }
    """

    result = schema.execute_sync(query)

    assert result.errors is None
    assert result.data["createUser"].get("name") is None

    if IS_PYDANTIC_V2:
        assert result.data["createUser"]["nameErrors"] == [
            ("String should have at least 2 characters")
        ]
    else:
        assert result.data["createUser"]["nameErrors"] == [
            ("ensure this value has at least 2 characters")
        ]
