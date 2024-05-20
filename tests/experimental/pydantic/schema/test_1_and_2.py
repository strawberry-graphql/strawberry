import textwrap
from typing import Optional, Union

import strawberry
from tests.experimental.pydantic.utils import needs_pydantic_v2


@needs_pydantic_v2
def test_can_use_both_pydantic_1_and_2():
    import pydantic
    from pydantic import v1 as pydantic_v1

    class UserModel(pydantic.BaseModel):
        age: int
        name: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age: strawberry.auto
        name: strawberry.auto

    class LegacyUserModel(pydantic_v1.BaseModel):
        age: int
        name: Optional[str]
        int_field: pydantic.v1.NonNegativeInt = 1

    @strawberry.experimental.pydantic.type(LegacyUserModel)
    class LegacyUser:
        age: strawberry.auto
        name: strawberry.auto
        int_field: strawberry.auto

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, id: strawberry.ID) -> Union[User, LegacyUser]:
            if id == "legacy":
                return LegacyUser(age=1, name="legacy")

            return User(age=1, name="ABC")

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type LegacyUser {
      age: Int!
      name: String
      intField: Int!
    }

    type Query {
      user(id: ID!): UserLegacyUser!
    }

    type User {
      age: Int!
      name: String
    }

    union UserLegacyUser = User | LegacyUser
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = """
        query ($id: ID!) {
            user(id: $id) {
                __typename
                ... on User { name }
                ... on LegacyUser { name }
            }
        }
    """

    result = schema.execute_sync(query, variable_values={"id": "new"})

    assert not result.errors
    assert result.data == {"user": {"__typename": "User", "name": "ABC"}}

    result = schema.execute_sync(query, variable_values={"id": "legacy"})

    assert not result.errors
    assert result.data == {"user": {"__typename": "LegacyUser", "name": "legacy"}}
