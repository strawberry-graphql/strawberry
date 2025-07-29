from textwrap import dedent
from typing import Optional, Union

import pytest

import strawberry


@pytest.fixture
def maybe_schema() -> strawberry.Schema:
    @strawberry.type
    class User:
        name: str
        phone: Optional[str]

    user = User(name="Patrick", phone=None)

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return user

    @strawberry.input
    class UpdateUserInput:
        phone: strawberry.Maybe[Union[str, None]]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update_user(self, input: UpdateUserInput) -> User:
            if input.phone:
                user.phone = input.phone.value
            return user

    return strawberry.Schema(query=Query, mutation=Mutation)


user_query = """
{
    user {
        phone
    }
}
"""


def set_phone(schema: strawberry.Schema, phone: Optional[str]) -> dict:
    query = """
    mutation ($phone: String) {
        updateUser(input: { phone: $phone }) {
            phone
        }
    }
    """

    result = schema.execute_sync(query, variable_values={"phone": phone})
    assert not result.errors
    assert result.data
    return result.data["updateUser"]


def get_user(schema: strawberry.Schema) -> dict:
    result = schema.execute_sync(user_query)
    assert not result.errors
    assert result.data
    return result.data["user"]


def test_maybe(maybe_schema: strawberry.Schema) -> None:
    assert get_user(maybe_schema)["phone"] is None
    res = set_phone(maybe_schema, "123")
    assert res["phone"] == "123"


def test_maybe_some_to_none(maybe_schema: strawberry.Schema) -> None:
    assert get_user(maybe_schema)["phone"] is None
    set_phone(maybe_schema, "123")
    res = set_phone(maybe_schema, None)
    assert res["phone"] is None


def test_maybe_absent_value(maybe_schema: strawberry.Schema) -> None:
    set_phone(maybe_schema, "123")

    query = """
    mutation {
        updateUser(input: {}) {
            phone
        }
    }
    """
    result = maybe_schema.execute_sync(query)
    assert not result.errors
    assert result.data
    assert result.data["updateUser"]["phone"] == "123"
    # now check the reverse case.

    set_phone(maybe_schema, None)
    result = maybe_schema.execute_sync(query)
    assert not result.errors
    assert result.data
    assert result.data["updateUser"]["phone"] is None


def test_optional_argument_maybe() -> None:
    @strawberry.type
    class Query:
        @strawberry.field
        def hello(self, name: strawberry.Maybe[Union[str, None]] = None) -> str:
            if name:
                return "None" if name.value is None else name.value

            return "UNSET"

    schema = strawberry.Schema(query=Query)

    assert str(schema) == dedent(
        """\
        type Query {
          hello(name: String): String!
        }"""
    )

    result = schema.execute_sync(
        """
        query {
            hello
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "UNSET"}
    result = schema.execute_sync(
        """
        query {
            hello(name: "bar")
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "bar"}
    result = schema.execute_sync(
        """
        query {
            hello(name: null)
        }
    """
    )
    assert not result.errors
    assert result.data == {"hello": "None"}


def test_maybe_list():
    @strawberry.input
    class InputData:
        items: strawberry.Maybe[Union[list[str], None]]

    @strawberry.type
    class Query:
        @strawberry.field
        def test(self, data: InputData) -> str:
            return "I am a test, and I received: " + str(data.items)

    schema = strawberry.Schema(Query)

    assert str(schema) == dedent(
        """\
        input InputData {
          items: [String!]
        }

        type Query {
          test(data: InputData!): String!
        }"""
    )
