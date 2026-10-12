from typing import Annotated, NewType

import pydantic
import pytest

import strawberry

UserId = NewType("UserId", int)


def test_unregistered_new_types_are_rejected_like_strawberry_types():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: UserId

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(id=UserId(1))

    with pytest.raises(
        TypeError,
        match=r"User fields cannot be resolved\. Unexpected type '.*\.UserId'",
    ):
        strawberry.Schema(query=Query)


def test_new_types_can_be_exposed_as_their_base_type():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: Annotated[UserId, strawberry.field(graphql_type=int)]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(id=UserId(1))

    schema = strawberry.Schema(query=Query)

    assert "id: Int!" in str(schema)

    result = schema.execute_sync("{ user { id } }")

    assert not result.errors
    assert result.data == {"user": {"id": 1}}
