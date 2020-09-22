from typing import Optional

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
            return User(age=1)

    schema = strawberry.Schema(query=Query)

    query = "{ user { age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1
