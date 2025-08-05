import dataclasses
import textwrap
from operator import getitem

import strawberry
from strawberry.printer import print_schema
from strawberry.schema.config import StrawberryConfig
from strawberry.types.field import StrawberryField


def test_custom_field():
    class CustomField(StrawberryField):
        def get_result(self, root, info, args, kwargs):
            return getattr(root, self.python_name) * 2

    @strawberry.type
    class Query:
        a: str = CustomField(default="Example")  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = "{ a }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data == {"a": "ExampleExample"}


def test_default_resolver_gets_attribute():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="Patrick")

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["user"]["name"] == "Patrick"


def test_can_change_default_resolver():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return {"name": "Patrick"}  # type: ignore

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(default_resolver=getitem),
    )

    query = "{ user { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["user"]["name"] == "Patrick"


def test_field_metadata():
    @strawberry.type
    class Query:
        a: str = strawberry.field(default="Example", metadata={"Foo": "Bar"})

    (a,) = dataclasses.fields(Query)
    assert a.metadata == {"Foo": "Bar"}


def test_field_type_priority():
    """Prioritise the field annotation on the class over the resolver annotation."""

    def my_resolver() -> str:
        return "1.33"

    @strawberry.type
    class Query:
        a: float = strawberry.field(resolver=my_resolver)

    schema = strawberry.Schema(Query)

    expected = """
    type Query {
      a: Float!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()

    query = "{ a }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data == {
        "a": 1.33,
    }


def test_field_type_override():
    @strawberry.type
    class Query:
        a: float = strawberry.field(graphql_type=str)
        b = strawberry.field(graphql_type=int)

        @strawberry.field(graphql_type=float)
        def c(self):
            return "3.4"

    schema = strawberry.Schema(Query)

    expected = """
    type Query {
      a: String!
      b: Int!
      c: Float!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()

    query = "{ a, b, c }"

    result = schema.execute_sync(query, root_value=Query(a=1.33, b=2))

    assert not result.errors
    assert result.data == {
        "a": "1.33",
        "b": 2,
        "c": 3.4,
    }


def test_field_type_default():
    @strawberry.type
    class User:
        name: str = "James"

    @strawberry.type
    class Query:
        @strawberry.field
        def a(self) -> User:
            return User()

    schema = strawberry.Schema(Query)

    expected = """
    type Query {
      a: User!
    }

    type User {
      name: String!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()
