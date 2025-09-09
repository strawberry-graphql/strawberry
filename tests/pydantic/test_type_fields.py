import pydantic
import strawberry
from strawberry.types.base import (
    get_object_definition,
)


def test_pydantic_field_descriptions():
    """Test that Pydantic field descriptions are preserved."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int = pydantic.Field(description="The user's age")
        name: str = pydantic.Field(description="The user's name")

    definition = get_object_definition(User, strict=True)

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.description == "The user's age"
    assert name_field.description == "The user's name"


def test_pydantic_field_aliases():
    """Test that Pydantic field aliases are used as GraphQL names."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int = pydantic.Field(alias="userAge")
        name: str = pydantic.Field(alias="userName")

    definition = get_object_definition(User, strict=True)

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.graphql_name == "userAge"
    assert name_field.graphql_name == "userName"
