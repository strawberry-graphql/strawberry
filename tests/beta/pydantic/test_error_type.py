from typing import List, Optional

import pydantic

import strawberry
from strawberry.types.types import TypeDefinition


def test_basic_error_type():
    class UserModel(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.beta.pydantic.error_type(UserModel, fields=["name", "age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "name"
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.type == str
    assert definition.fields[0].child.is_optional is False

    assert definition.fields[1].name == "age"
    assert definition.fields[1].is_list
    assert definition.fields[1].is_optional
    assert definition.fields[1].child.type == str
    assert definition.fields[1].child.is_optional is False


def test_error_type_with_nested_model():
    class FriendModel(pydantic.BaseModel):
        food: str

    class UserModel(pydantic.BaseModel):
        friend: FriendModel

    @strawberry.beta.pydantic.error_type(FriendModel, fields=["food"])
    class FriendError:
        pass

    @strawberry.beta.pydantic.error_type(UserModel, fields=["friend"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "friend"
    assert definition.fields[0].is_list is False
    assert definition.fields[0].is_optional
    assert definition.fields[0].type == FriendError


def test_error_type_with_list_nested_model():
    class FriendModel(pydantic.BaseModel):
        food: str

    class UserModel(pydantic.BaseModel):
        friends: List[FriendModel]

    @strawberry.beta.pydantic.error_type(FriendModel, fields=["food"])
    class FriendError:
        pass

    @strawberry.beta.pydantic.error_type(UserModel, fields=["friends"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "friends"
    assert definition.fields[0].is_list is True
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.type == FriendError
    assert definition.fields[0].child.is_optional


def test_error_type_with_list_of_scalar():
    class UserModel(pydantic.BaseModel):
        friends: List[int]

    @strawberry.beta.pydantic.error_type(UserModel, fields=["friends"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "friends"
    assert definition.fields[0].is_list is True
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.is_list is True
    assert definition.fields[0].child.is_optional
    assert definition.fields[0].child.child.type is str
    assert definition.fields[0].child.child.is_optional is False


def test_error_type_with_optional_field():
    class UserModel(pydantic.BaseModel):
        age: Optional[int]

    @strawberry.beta.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "age"
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.type == str
    assert definition.fields[0].child.is_optional is False


def test_error_type_with_list_of_optional_scalar():
    class UserModel(pydantic.BaseModel):
        age: List[Optional[int]]

    @strawberry.beta.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "age"
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.is_list
    assert definition.fields[0].child.is_optional
    assert definition.fields[0].child.child.type == str
    assert definition.fields[0].child.child.is_optional is False


def test_error_type_with_optional_list_scalar():
    class UserModel(pydantic.BaseModel):
        age: Optional[List[int]]

    @strawberry.beta.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "age"
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.is_list
    assert definition.fields[0].child.is_optional
    assert definition.fields[0].child.child.type == str
    assert definition.fields[0].child.child.is_optional is False


def test_error_type_with_optional_list_of_optional_scalar():
    class UserModel(pydantic.BaseModel):
        age: Optional[List[Optional[int]]]

    @strawberry.beta.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "age"
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.is_list
    assert definition.fields[0].child.is_optional
    assert definition.fields[0].child.child.type == str
    assert definition.fields[0].child.child.is_optional is False


def test_error_type_with_optional_list_of_nested_model():
    class FriendModel(pydantic.BaseModel):
        name: str

    @strawberry.beta.pydantic.error_type(FriendModel, fields=["name"])
    class FriendError(pydantic.BaseModel):
        pass

    class UserModel(pydantic.BaseModel):
        friends: Optional[List[FriendModel]]

    @strawberry.beta.pydantic.error_type(UserModel, fields=["friends"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "friends"
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional
    assert definition.fields[0].child.is_list is False
    assert definition.fields[0].child.is_optional
    assert definition.fields[0].child.type == FriendError


def test_error_type_with_matrix_list_of_scalar():
    class UserModel(pydantic.BaseModel):
        age: List[List[int]]

    @strawberry.beta.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "age"
    assert definition.fields[0].is_list
    assert definition.fields[0].is_optional

    assert definition.fields[0].child.is_list
    assert definition.fields[0].child.is_optional

    assert definition.fields[0].child.child.is_list
    assert definition.fields[0].child.child.is_optional

    assert definition.fields[0].child.child.is_list
    assert definition.fields[0].child.child.child.type == str
    assert definition.fields[0].child.child.child.is_optional is False
