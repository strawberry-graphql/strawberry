from typing import Union

import pydantic

import strawberry
from strawberry.experimental.pydantic._compat import IS_PYDANTIC_V2


def test_mutation():
    class User(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    @strawberry.experimental.pydantic.input(User)
    class CreateUserInput:
        name: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        name: strawberry.auto

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
    class User(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    @strawberry.experimental.pydantic.input(User)
    class CreateUserInput:
        name: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        name: strawberry.auto

    @strawberry.type
    class Query:
        h: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> UserType:
            data = input.to_pydantic()

            return UserType(name=data.name)

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
        assert result.errors[0].message.startswith(
            "1 validation error for User\n"
            "name\n"
            "  String should have at least 2 characters [type=string_too_short, "
            "input_value='P', input_type=str]\n"
        )
    else:
        assert result.errors[0].message == (
            "1 validation error for User\nname\n  ensure this value has at "
            "least 2 characters (type=value_error.any_str.min_length; limit_value=2)"
        )


def test_mutation_with_validation_of_nested_model():
    class HobbyInputModel(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    class CreateUserModel(pydantic.BaseModel):
        hobby: HobbyInputModel

    @strawberry.experimental.pydantic.input(HobbyInputModel)
    class HobbyInput:
        name: strawberry.auto

    @strawberry.experimental.pydantic.input(CreateUserModel)
    class CreateUserInput:
        hobby: strawberry.auto

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
            data = input.to_pydantic()

            return UserType(name=data.name)

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
        assert result.errors[0].message.startswith(
            "1 validation error for HobbyInputModel\n"
            "name\n"
            "  String should have at least 2 characters [type=string_too_short, "
            "input_value='P', input_type=str]\n"
        )

    else:
        assert result.errors[0].message == (
            "1 validation error for HobbyInputModel\nname\n"
            "  ensure this value has at least 2 characters "
            "(type=value_error.any_str.min_length; limit_value=2)"
        )


def test_mutation_with_validation_and_error_type():
    class User(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    @strawberry.experimental.pydantic.input(User)
    class CreateUserInput:
        name: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        name: strawberry.auto

    @strawberry.experimental.pydantic.error_type(User)
    class UserError:
        name: strawberry.auto

    @strawberry.type
    class Query:
        h: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> Union[UserType, UserError]:
            try:
                data = input.to_pydantic()
            except pydantic.ValidationError as e:
                args: dict[str, list[str]] = {}
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
