from textwrap import dedent

import pytest

import strawberry
from strawberry.tools import create_type


def test_create_decorator_type():
    @strawberry.field
    def name() -> str:
        return "foo"

    MyType = create_type("MyType", [name])
    definition = MyType._type_definition

    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "name"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == str


def test_create_variable_type():
    def get_name() -> str:
        return "foo"

    name = strawberry.field(name="name", resolver=get_name)

    MyType = create_type("MyType", [name])
    definition = MyType._type_definition

    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "get_name"
    assert definition.fields[0].graphql_name == "name"
    assert definition.fields[0].type == str


def test_create_type_empty_list():
    with pytest.raises(ValueError):
        create_type("MyType", [])


def test_create_type_field_no_name():
    name = strawberry.field()

    with pytest.raises(ValueError):
        create_type("MyType", [name])


def test_create_type_field_invalid():
    with pytest.raises(TypeError):
        create_type("MyType", [strawberry.type()])


def test_create_mutation_type():
    @strawberry.type
    class User:
        username: str

    @strawberry.mutation
    def make_user(info, username: str) -> User:
        return User(username=username)

    Mutation = create_type("Mutation", [make_user])
    definition = Mutation._type_definition

    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "make_user"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == User


def test_create_mutation_type_with_params():
    @strawberry.type
    class User:
        username: str

    @strawberry.mutation(name="makeNewUser", description="Make a new user")
    def make_user(info, username: str) -> User:
        return User(username=username)

    Mutation = create_type("Mutation", [make_user])
    definition = Mutation._type_definition

    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "make_user"
    assert definition.fields[0].graphql_name == "makeNewUser"
    assert definition.fields[0].type == User
    assert definition.fields[0].description == "Make a new user"


def test_create_schema():
    @strawberry.type
    class User:
        id: strawberry.ID

    @strawberry.field
    def get_user_by_id(info, id: strawberry.ID) -> User:
        return User(id=id)

    Query = create_type("Query", [get_user_by_id])

    schema = strawberry.Schema(query=Query)

    sdl = """
    type Query {
      getUserById(id: ID!): User!
    }

    type User {
      id: ID!
    }
    """

    assert dedent(sdl).strip() == str(schema)

    result = schema.execute_sync(
        """
        {
            getUserById(id: "TEST") {
                id
            }
        }
    """
    )

    assert not result.errors
    assert result.data == {"getUserById": {"id": "TEST"}}
