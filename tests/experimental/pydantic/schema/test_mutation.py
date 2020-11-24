import pydantic

import strawberry


def test_mutation():
    class User(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    @strawberry.experimental.pydantic.input(User, fields=["name"])
    class CreateUserInput:
        pass

    @strawberry.experimental.pydantic.type(User, fields=["name"])
    class UserType:
        pass

    @strawberry.type
    class Query:
        h: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> UserType:
            return UserType(input.name)

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

    @strawberry.experimental.pydantic.input(User, fields=["name"])
    class CreateUserInput:
        pass

    @strawberry.experimental.pydantic.type(User, fields=["name"])
    class UserType:
        pass

    @strawberry.type
    class Query:
        h: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> UserType:
            data = input.to_pydantic()

            return UserType(data.name)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
        mutation {
            createUser(input: { name: "P" }) {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert result.errors[0].message == (
        "1 validation error for User\nname\n  ensure this value has at "
        "least 2 characters (type=value_error.any_str.min_length; limit_value=2)"
    )


def test_mutation_with_validation_of_nested_model():
    class HobbyInputModel(pydantic.BaseModel):
        name: pydantic.constr(min_length=2)

    class CreateUserModel(pydantic.BaseModel):
        hobby: HobbyInputModel

    @strawberry.experimental.pydantic.input(HobbyInputModel, fields=["name"])
    class HobbyInput:
        pass

    @strawberry.experimental.pydantic.input(CreateUserModel, fields=["hobby"])
    class CreateUserInput:
        pass

    class UserModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(UserModel, fields=["name"])
    class UserType:
        pass

    @strawberry.type
    class Query:
        h: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_user(self, input: CreateUserInput) -> UserType:
            data = input.to_pydantic()

            return UserType(data.name)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
        mutation {
            createUser(input: { hobby: { name: "P" } }) {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert result.errors[0].message == (
        "1 validation error for CreateUserModel\nhobby -> name\n"
        "  ensure this value has at least 2 characters "
        "(type=value_error.any_str.min_length; limit_value=2)"
    )
