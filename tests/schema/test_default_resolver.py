from operator import getitem

import strawberry
from strawberry.schema.config import StrawberryConfig


def test_default_resolver_gets_attribute():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="Patrick")

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["user"]["name"] == "Patrick"


def test_can_change_default_resolver():
    @strawberry.type
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return {"name": "Patrick"}  # type: ignore

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(default_resolver=getitem),
    )

    query = "{ user { name } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["user"]["name"] == "Patrick"
