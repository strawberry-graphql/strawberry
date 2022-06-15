from pydantic import BaseModel, Field

import strawberry


def test_use_alias_as_gql_name():
    class UserModel(BaseModel):
        age_: int = Field(..., alias="age_alias")

    @strawberry.experimental.pydantic.type(
        UserModel, all_fields=True, use_pydantic_alias=True
    )
    class User:
        ...

    @strawberry.type
    class Query:
        user: User = User(age_=5)

    schema = strawberry.Schema(query=Query)
    query = """{
        user {
            __typename,

            ... on User {
                age_alias
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["user"] == {"__typename": "User", "age_alias": 5}


def test_do_not_use_alias_as_gql_name():
    class UserModel(BaseModel):
        age_: int = Field(..., alias="age_alias")

    @strawberry.experimental.pydantic.type(
        UserModel, all_fields=True, use_pydantic_alias=False
    )
    class User:
        ...

    @strawberry.type
    class Query:
        user: User = User(age_=5)

    schema = strawberry.Schema(query=Query)
    query = """{
        user {
            __typename,

            ... on User {
                age_
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["user"] == {"__typename": "User", "age_": 5}
