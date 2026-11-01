import textwrap

import strawberry
from strawberry.printer import print_schema
from strawberry.schema.config import StrawberryConfig


def test_sort_schema_export():
    @strawberry.type
    class User:
        z_field: str
        a_field: int

    @strawberry.type
    class Query:
        c_user: User
        a_hello: str
        b_number: int

    @strawberry.type
    class Mutation:
        z_action: str
        a_action: str

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        config=StrawberryConfig(sort_schema=True),
    )

    expected = """
    type Mutation {
      aAction: String!
      zAction: String!
    }

    type Query {
      aHello: String!
      bNumber: Int!
      cUser: User!
    }

    type User {
      aField: Int!
      zField: String!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()


def test_sort_schema_introspection():
    @strawberry.type
    class Query:
        c_field: str
        a_field: str
        b_field: str

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(sort_schema=True),
    )

    query = """
    {
      __schema {
        queryType {
          fields {
            name
          }
        }
      }
    }
    """

    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data == {
        "__schema": {
            "queryType": {
                "fields": [
                    {"name": "aField"},
                    {"name": "bField"},
                    {"name": "cField"},
                ]
            }
        }
    }
