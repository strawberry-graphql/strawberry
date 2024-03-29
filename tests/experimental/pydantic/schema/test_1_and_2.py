import textwrap
from typing import Optional, Union

import pytest

import strawberry
from tests.experimental.pydantic.utils import needs_pydantic_v2


@needs_pydantic_v2
@pytest.mark.xfail
def test_can_use_both_pydantic_1_and_2():
    import pydantic
    from pydantic import v1 as pydantic_v1

    class UserModel(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age: strawberry.auto
        password: strawberry.auto

    class LegacyUserModel(pydantic_v1.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(LegacyUserModel)
    class LegacyUser:
        age: strawberry.auto
        password: strawberry.auto

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> Union[User, LegacyUser]:
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

    type LegacyUser {
      age: Int!
      password: String
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1
