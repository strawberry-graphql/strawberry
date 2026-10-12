"""
Query and mutation execution tests for Pydantic integration.

These tests verify that Pydantic models work correctly in GraphQL queries and mutations.
"""

from typing import Optional

import pydantic
from inline_snapshot import snapshot

import strawberry


def test_basic_query_execution():
    """Test basic query execution with Pydantic types."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(name="John", age=30)

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            getUser {
                name
                age
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot({"getUser": {"name": "John", "age": 30}})


def test_query_with_optional_fields():
    """Test query execution with optional fields."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        email: Optional[str] = None
        age: Optional[int] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(name="John", email="john@example.com")

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            getUser {
                name
                email
                age
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot(
        {"getUser": {"name": "John", "email": "john@example.com", "age": None}}
    )
