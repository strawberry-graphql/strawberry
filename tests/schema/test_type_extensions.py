import textwrap

import pytest

import strawberry
from strawberry.printer import print_schema


def test_object_extension_can_extend_existing_type():
    @strawberry.type(name="User")
    class User:
        name: str

    @strawberry.type(name="User", extend=True)
    class UserExtension:
        @strawberry.field
        def extra(self) -> str:
            return self.extra

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            user = User(name="Ada")
            user.extra = "Lovelace"
            return user

    schema = strawberry.Schema(query=Query, types=[UserExtension])

    expected = """
    type Query {
      user: User!
    }

    type User {
      name: String!
    }

    extend type User {
      extra: String!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()

    result = schema.execute_sync("{ user { name extra } }")

    assert not result.errors
    assert result.data == {"user": {"name": "Ada", "extra": "Lovelace"}}


def test_object_extension_rejects_duplicate_fields():
    @strawberry.type(name="User")
    class User:
        name: str

    @strawberry.type(name="User", extend=True)
    class UserExtension:
        name: str

    @strawberry.type
    class Query:
        user: User

    with pytest.raises(
        TypeError,
        match="Type User defines duplicate extension field\\(s\\): name",
    ):
        strawberry.Schema(query=Query, types=[UserExtension])
