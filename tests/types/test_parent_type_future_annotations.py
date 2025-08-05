from __future__ import annotations

import textwrap

import strawberry


def test_parent_type():
    global User

    try:

        def get_full_name(user: strawberry.Parent[User]) -> str:
            return f"{user.first_name} {user.last_name}"

        @strawberry.type
        class User:
            first_name: str
            last_name: str
            full_name: str = strawberry.field(resolver=get_full_name)

        @strawberry.type
        class Query:
            @strawberry.field
            def user(self) -> User:
                return User(first_name="John", last_name="Doe")  # noqa: F821

        schema = strawberry.Schema(query=Query)

        expected = """\
            type Query {
              user: User!
            }

            type User {
              firstName: String!
              lastName: String!
              fullName: String!
            }
        """
        assert textwrap.dedent(str(schema)).strip() == textwrap.dedent(expected).strip()

        query = "{ user { firstName, lastName, fullName } }"
        result = schema.execute_sync(query)
        assert not result.errors
        assert result.data == {
            "user": {
                "firstName": "John",
                "lastName": "Doe",
                "fullName": "John Doe",
            }
        }
    finally:
        del User
