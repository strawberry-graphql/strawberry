from typing import Annotated

import pytest
from inline_snapshot import snapshot

import pydantic
import strawberry
from strawberry.pydantic.exceptions import UnregisteredTypeException
from strawberry.types.base import get_object_definition


def test_pydantic_field_descriptions():
    """Test that Pydantic field descriptions are preserved."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: Annotated[int, pydantic.Field(description="The user's age")]
        name: Annotated[str, pydantic.Field(description="The user's name")]

    definition = get_object_definition(User, strict=True)

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.description == "The user's age"
    assert name_field.description == "The user's name"


def test_pydantic_field_aliases():
    """Test that Pydantic field aliases are used as GraphQL names."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: Annotated[int, pydantic.Field(alias="userAge")]
        name: Annotated[str, pydantic.Field(alias="userName")]

    definition = get_object_definition(User, strict=True)

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.graphql_name == "userAge"
    assert name_field.graphql_name == "userName"


def test_can_use_strawberry_types():
    """Test that Pydantic models can use Strawberry types."""

    @strawberry.type
    class Address:
        street: str
        city: str

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str
        address: Address

    definition = get_object_definition(User, strict=True)

    address_field = next(f for f in definition.fields if f.python_name == "address")

    assert address_field.type is Address

    @strawberry.type
    class Query:
        @strawberry.field
        @staticmethod
        def user() -> User:
            return User(
                name="Rabbit", address=Address(street="123 Main St", city="Wonderland")
            )

    schema = strawberry.Schema(query=Query)

    query = """query {
        user {
            name
            address {
                street
                city
            }
        }
    }"""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot(
        {
            "user": {
                "name": "Rabbit",
                "address": {"street": "123 Main St", "city": "Wonderland"},
            }
        }
    )


def test_all_models_need_to_marked_as_strawberry_types():
    class Address(pydantic.BaseModel):
        street: str
        city: str

    with pytest.raises(
        UnregisteredTypeException,
        match=(
            r"Cannot find a Strawberry Type for <class '([^']+)\.([^']+)'> did you forget to register it\?"
        ),
    ):

        @strawberry.pydantic.type
        class User(pydantic.BaseModel):
            name: str
            address: Address
