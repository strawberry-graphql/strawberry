import textwrap

import pydantic
import pytest
from pydantic.version import VERSION as PYDANTIC_VERSION

import strawberry

IS_PYDANTIC_V2: bool = PYDANTIC_VERSION.startswith("2.")

if IS_PYDANTIC_V2:
    from pydantic import computed_field


@pytest.mark.skipif(
    not IS_PYDANTIC_V2, reason="Requires Pydantic v2 for computed_field"
)
def test_computed_field():
    class UserModel(pydantic.BaseModel):
        age: int

        @computed_field
        @property
        def next_age(self) -> int:
            return self.age + 1

    @strawberry.experimental.pydantic.type(
        UserModel, all_fields=True, include_computed=True
    )
    class User:
        pass

    @strawberry.experimental.pydantic.type(UserModel, all_fields=True)
    class UserNoComputed:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User.from_pydantic(UserModel(age=1))

        @strawberry.field
        def user_no_computed(self) -> UserNoComputed:
            return UserNoComputed.from_pydantic(UserModel(age=1))

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Query {
      user: User!
      userNoComputed: UserNoComputed!
    }

    type User {
      age: Int!
      nextAge: Int!
    }

    type UserNoComputed {
      age: Int!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { age nextAge } }"

    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data["user"]["age"] == 1
    assert result.data["user"]["nextAge"] == 2
