from typing import Optional

import pydantic
from inline_snapshot import snapshot

import strawberry
from strawberry.types.base import (
    StrawberryOptional,
    get_object_definition,
)


def test_basic_type_includes_all_fields():
    """Test that @strawberry.pydantic.type includes all fields from the model."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    definition = get_object_definition(User, strict=True)
    assert definition.name == "User"

    # Should have two fields
    assert len(definition.fields) == 2

    # Find fields by name
    age_field = next(f for f in definition.fields if f.python_name == "age")
    password_field = next(f for f in definition.fields if f.python_name == "password")

    assert age_field.python_name == "age"
    assert age_field.graphql_name is None
    assert age_field.type is int

    assert password_field.python_name == "password"
    assert password_field.graphql_name is None
    assert isinstance(password_field.type, StrawberryOptional)
    assert password_field.type.of_type is str


def test_basic_type_with_name_override():
    """Test that @strawberry.pydantic.type with name parameter works."""

    @strawberry.pydantic.type(name="CustomUser")
    class User(pydantic.BaseModel):
        age: int

    definition = get_object_definition(User, strict=True)
    assert definition.name == "CustomUser"


def test_basic_type_with_description():
    """Test that @strawberry.pydantic.type with description parameter works."""

    @strawberry.pydantic.type(description="A user model")
    class User(pydantic.BaseModel):
        age: int

    definition = get_object_definition(User, strict=True)
    assert definition.description == "A user model"


def test_is_type_of_method():
    """Test that is_type_of method is added for proper type resolution."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        name: str

    # Check that is_type_of method exists
    assert hasattr(User, "is_type_of")
    assert callable(User.is_type_of)

    # Test type checking
    user_instance = User(age=25, name="John")
    assert User.is_type_of(user_instance, None) is True

    # Test with different type
    class Other:
        pass

    other_instance = Other()
    assert User.is_type_of(other_instance, None) is False


def test_schema_generation():
    """Test that the decorated models work in schema generation."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        name: str

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        age: int
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(age=25, name="John")

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: CreateUserInput) -> User:
            return User(age=input.age, name=input.name)

    # Test that schema can be created successfully
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    assert schema is not None

    assert str(schema) == snapshot(
        """\
input CreateUserInput {
  age: Int!
  name: String!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
}

type Query {
  getUser: User!
}

type User {
  age: Int!
  name: String!
}\
"""
    )
