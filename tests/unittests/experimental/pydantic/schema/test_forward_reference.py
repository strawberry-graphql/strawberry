from __future__ import annotations

import textwrap
from typing import Optional

import pydantic

import strawberry


def test_auto_fields():
    global User

    class UserModel(pydantic.BaseModel):
        age: int
        password: Optional[str]
        other: float

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age: strawberry.auto
        password: strawberry.auto

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(age=1, password="ABC")

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Query {
      user: User!
    }

    type User {
      age: Int!
      password: String
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1
