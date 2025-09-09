from typing import Generic, TypeVar

from inline_snapshot import snapshot

import pydantic
import strawberry
from strawberry.types.base import (
    StrawberryTypeVar,
    get_object_definition,
)

T = TypeVar("T")


def test_basic_pydantic_generic_fields():
    """Test that pydantic generic models preserve field types correctly."""

    @strawberry.pydantic.type
    class GenericModel(pydantic.BaseModel, Generic[T]):
        value: T
        name: str = "default"

    definition = get_object_definition(GenericModel, strict=True)

    # Check fields
    fields = definition.fields
    assert len(fields) == 2

    value_field = next(f for f in fields if f.python_name == "value")
    name_field = next(f for f in fields if f.python_name == "name")

    # The value field should contain a TypeVar (generic parameter)
    assert isinstance(value_field.type, StrawberryTypeVar)
    assert value_field.type.type_var is T

    # The name field should be concrete
    assert name_field.type is str


def test_pydantic_generic_with_concrete_type():
    """Test pydantic with a concrete generic instantiation."""

    class GenericModel(pydantic.BaseModel, Generic[T]):
        data: T

    # Create a concrete version by inheriting from GenericModel[int]
    @strawberry.pydantic.type
    class ConcreteModel(GenericModel[int]):
        pass

    definition = get_object_definition(ConcreteModel, strict=True)

    # Verify the field type is concrete
    [data_field] = definition.fields
    assert data_field.python_name == "data"
    assert data_field.type is int


def test_pydantic_generic_schema():
    """Test the GraphQL schema generated from pydantic generic types."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel, Generic[T]):
        id: int
        data: T
        name: str = "default"

    # Create concrete versions
    @strawberry.pydantic.type
    class UserString(User[str]):
        pass

    @strawberry.pydantic.type
    class UserInt(User[int]):
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user_string(self) -> UserString:
            return UserString(id=1, data="hello", name="test")

        @strawberry.field
        def get_user_int(self) -> UserInt:
            return UserInt(id=2, data=42, name="test")

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Query {
  getUserString: UserString!
  getUserInt: UserInt!
}

type UserInt {
  id: Int!
  data: Int!
  name: String!
}

type UserString {
  id: Int!
  data: String!
  name: String!
}\
""")
