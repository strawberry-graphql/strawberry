from typing import List, Optional

import pydantic
import strawberry


def test_basic_type():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.pydantic.type(User)
    class UserType:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(age=1, password="ABC")

    schema = strawberry.Schema(query=Query)

    query = "{ user { age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1


def test_basic_type_with_list():
    class User(pydantic.BaseModel):
        age: int
        friend_names: List[str]

    @strawberry.pydantic.type(User)
    class UserType:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(age=1, friend_names=["A", "B"])

    schema = strawberry.Schema(query=Query)

    query = "{ user { friendNames } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["friendNames"] == ["A", "B"]
