"""
Tests for basic Pydantic integration functionality.

These tests verify that Pydantic models can be directly decorated with
@strawberry.pydantic.type decorators and work correctly as GraphQL types.
"""

from typing import Optional

import pydantic
import strawberry
from strawberry.types.base import StrawberryObjectDefinition, StrawberryOptional


def test_basic_type_includes_all_fields():
    """Test that @strawberry.pydantic.type includes all fields from the model."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    definition: StrawberryObjectDefinition = User.__strawberry_definition__
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


def test_basic_type_with_multiple_fields():
    """Test that @strawberry.pydantic.type works with multiple fields."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        name: str

    definition: StrawberryObjectDefinition = User.__strawberry_definition__
    assert definition.name == "User"

    # Should have three fields
    assert len(definition.fields) == 3

    field_names = {f.python_name for f in definition.fields}
    assert field_names == {"age", "password", "name"}


def test_basic_type_with_name_override():
    """Test that @strawberry.pydantic.type with name parameter works."""

    @strawberry.pydantic.type(name="CustomUser")
    class User(pydantic.BaseModel):
        age: int

    definition: StrawberryObjectDefinition = User.__strawberry_definition__
    assert definition.name == "CustomUser"


def test_basic_type_with_description():
    """Test that @strawberry.pydantic.type with description parameter works."""

    @strawberry.pydantic.type(description="A user model")
    class User(pydantic.BaseModel):
        age: int

    definition: StrawberryObjectDefinition = User.__strawberry_definition__
    assert definition.description == "A user model"


def test_basic_input_type():
    """Test that @strawberry.pydantic.input works."""

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        age: int
        name: str

    definition: StrawberryObjectDefinition = CreateUserInput.__strawberry_definition__
    assert definition.name == "CreateUserInput"
    assert definition.is_input is True
    assert len(definition.fields) == 2


def test_basic_interface_type():
    """Test that @strawberry.pydantic.interface works."""

    @strawberry.pydantic.interface
    class Node(pydantic.BaseModel):
        id: str

    definition: StrawberryObjectDefinition = Node.__strawberry_definition__
    assert definition.name == "Node"
    assert definition.is_interface is True
    assert len(definition.fields) == 1


def test_pydantic_field_descriptions():
    """Test that Pydantic field descriptions are preserved."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int = pydantic.Field(description="The user's age")
        name: str = pydantic.Field(description="The user's name")

    definition: StrawberryObjectDefinition = User.__strawberry_definition__

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.description == "The user's age"
    assert name_field.description == "The user's name"


def test_pydantic_field_aliases():
    """Test that Pydantic field aliases are used as GraphQL names."""

    @strawberry.pydantic.type(use_pydantic_alias=True)
    class User(pydantic.BaseModel):
        age: int = pydantic.Field(alias="userAge")
        name: str = pydantic.Field(alias="userName")

    definition: StrawberryObjectDefinition = User.__strawberry_definition__

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.graphql_name == "userAge"
    assert name_field.graphql_name == "userName"


def test_pydantic_field_aliases_disabled():
    """Test that Pydantic field aliases can be disabled."""

    @strawberry.pydantic.type(use_pydantic_alias=False)
    class User(pydantic.BaseModel):
        age: int = pydantic.Field(alias="userAge")
        name: str = pydantic.Field(alias="userName")

    definition: StrawberryObjectDefinition = User.__strawberry_definition__

    age_field = next(f for f in definition.fields if f.python_name == "age")
    name_field = next(f for f in definition.fields if f.python_name == "name")

    assert age_field.graphql_name is None
    assert name_field.graphql_name is None


def test_basic_type_includes_all_pydantic_fields():
    """Test that the decorator includes all Pydantic fields."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        name: str

    definition: StrawberryObjectDefinition = User.__strawberry_definition__

    # Should have age and name from the model
    field_names = {f.python_name for f in definition.fields}
    assert "age" in field_names
    assert "name" in field_names
    assert len(field_names) == 2


def test_conversion_methods_exist():
    """Test that from_pydantic and to_pydantic methods are added to the class."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int
        name: str

    # Check that conversion methods exist
    assert hasattr(User, "from_pydantic")
    assert hasattr(User, "to_pydantic")
    assert callable(User.from_pydantic)
    assert callable(User.to_pydantic)

    # Test basic conversion
    original = User(age=25, name="John")
    converted = User.from_pydantic(original)
    assert converted.age == 25
    assert converted.name == "John"

    # Test back conversion
    back_converted = converted.to_pydantic()
    assert back_converted.age == 25
    assert back_converted.name == "John"


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


def test_strawberry_type_registration():
    """Test that _strawberry_type is registered on the BaseModel."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int

    assert hasattr(User, "_strawberry_type")
    assert User._strawberry_type is User


def test_strawberry_input_type_registration():
    """Test that _strawberry_input_type is registered on input BaseModels."""

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        age: int

    assert hasattr(CreateUserInput, "_strawberry_input_type")
    assert CreateUserInput._strawberry_input_type is CreateUserInput


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

    # Test that the schema string can be generated
    schema_str = str(schema)
    assert "type User" in schema_str
    assert "input CreateUserInput" in schema_str
