from typing import List, Optional

import pytest

import pydantic

import strawberry
from strawberry.experimental.pydantic.exceptions import MissingFieldsListError
from strawberry.type import StrawberryList, StrawberryOptional
from strawberry.types.types import TypeDefinition


def test_basic_error_type_fields():
    class UserModel(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["name", "age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field1, field2] = definition.fields

    assert field1.python_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert isinstance(field1.type.of_type, StrawberryList)
    assert field1.type.of_type.of_type is str

    assert definition.fields[1].python_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert isinstance(field2.type.of_type, StrawberryList)
    assert field1.type.of_type.of_type is str


def test_basic_error_type():
    class UserModel(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        name: strawberry.auto
        age: strawberry.auto

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field1, field2] = definition.fields

    assert field1.python_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert isinstance(field1.type.of_type, StrawberryList)
    assert field1.type.of_type.of_type is str

    assert definition.fields[1].python_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert isinstance(field2.type.of_type, StrawberryList)
    assert field1.type.of_type.of_type is str


def test_basic_error_type_all_fields():
    class UserModel(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.experimental.pydantic.error_type(UserModel, all_fields=True)
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field1, field2] = definition.fields

    assert field1.python_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert isinstance(field1.type.of_type, StrawberryList)
    assert field1.type.of_type.of_type is str

    assert definition.fields[1].python_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert isinstance(field2.type.of_type, StrawberryList)
    assert field1.type.of_type.of_type is str


@pytest.mark.filterwarnings("error")
def test_basic_type_all_fields_warn():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    with pytest.raises(
        UserWarning,
        match=("Using all_fields overrides any explicitly defined fields"),
    ):

        @strawberry.experimental.pydantic.error_type(User, all_fields=True)
        class UserError:
            age: strawberry.auto


def test_basic_error_type_without_fields_throws_an_error():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    with pytest.raises(MissingFieldsListError):

        @strawberry.experimental.pydantic.error_type(User)
        class UserError:
            pass


def test_error_type_with_default_value():
    class UserModel(pydantic.BaseModel):
        name: str = "foo"
        age: int

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        name: strawberry.auto
        age: strawberry.auto

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field1, field2] = definition.fields

    assert field1.python_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert isinstance(field1.type.of_type, StrawberryList)
    assert field1.type.of_type.of_type is str
    assert field1.default is None

    assert field2.python_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert isinstance(field2.type.of_type, StrawberryList)
    assert field2.type.of_type.of_type is str
    assert field2.default is None


def test_error_type_with_nested_model():
    class FriendModel(pydantic.BaseModel):
        food: str

    class UserModel(pydantic.BaseModel):
        friend: FriendModel

    @strawberry.experimental.pydantic.error_type(FriendModel)
    class FriendError:
        food: strawberry.auto

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        friend: strawberry.auto

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field] = definition.fields

    assert field.python_name == "friend"
    assert isinstance(field.type, StrawberryOptional)
    assert field.type.of_type is FriendError


def test_error_type_with_list_nested_model():
    class FriendModel(pydantic.BaseModel):
        food: str

    class UserModel(pydantic.BaseModel):
        friends: List[FriendModel]

    @strawberry.experimental.pydantic.error_type(FriendModel)
    class FriendError:
        food: strawberry.auto

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        friends: strawberry.auto

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field] = definition.fields

    assert field.python_name == "friends"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert field.type.of_type.of_type.of_type is FriendError


def test_error_type_with_list_of_scalar():
    class UserModel(pydantic.BaseModel):
        friends: List[int]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        friends: strawberry.auto

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field] = definition.fields

    assert field.python_name == "friends"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)
    assert field.type.of_type.of_type.of_type.of_type is str


def test_error_type_with_optional_field():
    class UserModel(pydantic.BaseModel):
        age: Optional[int]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        age: strawberry.auto

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field] = definition.fields

    assert field.python_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is str


def test_error_type_with_list_of_optional_scalar():
    class UserModel(pydantic.BaseModel):
        age: List[Optional[int]]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        age: strawberry.auto

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.python_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)
    assert field.type.of_type.of_type.of_type.of_type is str


def test_error_type_with_optional_list_scalar():
    class UserModel(pydantic.BaseModel):
        age: Optional[List[int]]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        age: strawberry.auto

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.python_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)
    assert field.type.of_type.of_type.of_type.of_type is str


def test_error_type_with_optional_list_of_optional_scalar():
    class UserModel(pydantic.BaseModel):
        age: Optional[List[Optional[int]]]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        age: strawberry.auto

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.python_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)
    assert field.type.of_type.of_type.of_type.of_type is str


def test_error_type_with_optional_list_of_nested_model():
    class FriendModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.error_type(FriendModel)
    class FriendError:
        name: strawberry.auto

    class UserModel(pydantic.BaseModel):
        friends: Optional[List[FriendModel]]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        friends: strawberry.auto

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.python_name == "friends"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert field.type.of_type.of_type.of_type is FriendError


def test_error_type_with_matrix_list_of_scalar():
    class UserModel(pydantic.BaseModel):
        age: List[List[int]]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        age: strawberry.auto

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.python_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)

    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)

    assert isinstance(field.type.of_type.of_type.of_type.of_type, StrawberryOptional)
    assert isinstance(
        field.type.of_type.of_type.of_type.of_type.of_type, StrawberryList
    )

    assert field.type.of_type.of_type.of_type.of_type.of_type.of_type is str
