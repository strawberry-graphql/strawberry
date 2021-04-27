from textwrap import dedent

import strawberry
from strawberry.tools import create_type


def test_create_basic_type():
    @strawberry.field
    def name() -> str:
        return "foo"

    MyType = create_type("MyType", [name])
    definition = MyType._type_definition

    assert len(definition.fields) == 1

    assert definition.fields[0].graphql_name == "name"
    assert definition.fields[0].type == str


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

    assert definition.fields[0].graphql_name == "makeUser"
    assert definition.fields[0].type == User


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
