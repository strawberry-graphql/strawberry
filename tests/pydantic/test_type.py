import sys
from collections.abc import Callable
from typing import Optional

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.pydantic.exceptions import (
    ModelAlreadyDecoratedError,
    NotAPydanticModelError,
)
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


@pytest.mark.parametrize(
    "decorator",
    [
        strawberry.pydantic.type,
        strawberry.pydantic.input,
        strawberry.pydantic.interface,
    ],
    ids=["type", "input", "interface"],
)
def test_decorating_a_class_that_is_not_a_pydantic_model_raises_an_error(
    decorator: Callable[[type], type],
):
    name = decorator.__name__

    with pytest.raises(
        NotAPydanticModelError,
        match=(
            rf"strawberry\.pydantic\.{name} can only be used with pydantic models, "
            r"but `User` is not a subclass of `pydantic\.BaseModel`"
        ),
    ):

        @decorator
        class User:
            name: str


def test_decorating_a_pydantic_dataclass_raises_an_error():
    with pytest.raises(NotAPydanticModelError, match="`User` is not a subclass"):

        @strawberry.pydantic.type
        @pydantic.dataclasses.dataclass
        class User:
            name: str


@pytest.mark.skipif(
    sys.version_info >= (3, 14),
    reason="Pydantic v1 is not compatible with Python 3.14+",
)
def test_decorating_a_pydantic_v1_model_raises_an_error():
    from pydantic import v1 as pydantic_v1

    with pytest.raises(
        NotAPydanticModelError,
        match=(
            r"`User` is a pydantic v1 model, but strawberry\.pydantic\.type only "
            r"supports pydantic v2 models"
        ),
    ):

        @strawberry.pydantic.type
        class User(pydantic_v1.BaseModel):
            name: str


def test_models_can_only_be_decorated_once():
    @strawberry.pydantic.type
    class Address(pydantic.BaseModel):
        street: str

    with pytest.raises(
        ModelAlreadyDecoratedError,
        match=(
            r"`Address` is already a type, so it can't be decorated with "
            r"`strawberry\.pydantic\.input`"
        ),
    ):
        strawberry.pydantic.input(Address)

    # a subclass can be used as the input
    @strawberry.pydantic.input
    class AddressInput(Address):
        pass

    assert get_object_definition(AddressInput, strict=True).is_input
    assert not get_object_definition(Address, strict=True).is_input
