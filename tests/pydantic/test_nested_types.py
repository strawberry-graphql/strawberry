"""
Nested type tests for Pydantic integration.

These tests verify that nested Pydantic types work correctly in GraphQL.
"""

from typing import Optional

from inline_snapshot import snapshot

import pydantic
import strawberry


def test_nested_pydantic_types():
    """Test nested Pydantic types in queries."""

    @strawberry.pydantic.type
    class Address(pydantic.BaseModel):
        street: str
        city: str
        zipcode: str

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int
        address: Address

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(
                name="John",
                age=30,
                address=Address(street="123 Main St", city="Anytown", zipcode="12345"),
            )

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            getUser {
                name
                age
                address {
                    street
                    city
                    zipcode
                }
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot(
        {
            "getUser": {
                "name": "John",
                "age": 30,
                "address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "zipcode": "12345",
                },
            }
        }
    )


def test_list_of_pydantic_types():
    """Test lists of Pydantic types."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.type
    class Query:
        @strawberry.field
        def get_users(self) -> list[User]:
            return [
                User(name="John", age=30),
                User(name="Jane", age=25),
                User(name="Bob", age=35),
            ]

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            getUsers {
                name
                age
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot(
        {
            "getUsers": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25},
                {"name": "Bob", "age": 35},
            ]
        }
    )


def test_complex_pydantic_types_execution():
    """Test complex Pydantic types with various field types."""

    @strawberry.pydantic.type
    class Profile(pydantic.BaseModel):
        bio: Optional[str] = None
        website: Optional[str] = None

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        email: str
        is_active: bool
        tags: list[str] = []
        profile: Optional[Profile] = None

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(
                id=1,
                name="John Doe",
                email="john@example.com",
                is_active=True,
                tags=["developer", "python", "graphql"],
                profile=Profile(
                    bio="Software developer", website="https://johndoe.com"
                ),
            )

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            getUser {
                id
                name
                email
                isActive
                tags
                profile {
                    bio
                    website
                }
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot(
        {
            "getUser": {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "isActive": True,
                "tags": ["developer", "python", "graphql"],
                "profile": {
                    "bio": "Software developer",
                    "website": "https://johndoe.com",
                },
            }
        }
    )
