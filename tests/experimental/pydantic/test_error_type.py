from typing import List, Optional

import pydantic

import strawberry
from strawberry.type import StrawberryOptional, StrawberryList
from strawberry.types.types import TypeDefinition


def test_basic_error_type():
    class UserModel(pydantic.BaseModel):
        name: str
        age: int

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["name", "age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field1, field2] = definition.fields

    assert field1.graphql_name == "name"
    assert isinstance(field1.type, StrawberryOptional)
    assert isinstance(field1.type.of_type, StrawberryList)
    assert field1.type.of_type.of_type is str

    assert definition.fields[1].graphql_name == "age"
    assert isinstance(field2.type, StrawberryOptional)
    assert isinstance(field2.type.of_type, StrawberryList)
    assert field1.type.of_type.of_type is str


def test_error_type_with_nested_model():
    class FriendModel(pydantic.BaseModel):
        food: str

    class UserModel(pydantic.BaseModel):
        friend: FriendModel

    @strawberry.experimental.pydantic.error_type(FriendModel, fields=["food"])
    class FriendError:
        pass

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["friend"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field] = definition.fields

    assert field.graphql_name == "friend"
    assert isinstance(field.type, StrawberryOptional)
    assert field.type.of_type is FriendError


def test_error_type_with_list_nested_model():
    class FriendModel(pydantic.BaseModel):
        food: str

    class UserModel(pydantic.BaseModel):
        friends: List[FriendModel]

    @strawberry.experimental.pydantic.error_type(FriendModel, fields=["food"])
    class FriendError:
        pass

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["friends"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field] = definition.fields

    assert field.graphql_name == "friends"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert field.type.of_type.of_type.of_type is FriendError


def test_error_type_with_list_of_scalar():
    class UserModel(pydantic.BaseModel):
        friends: List[int]

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["friends"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field] = definition.fields

    assert field.graphql_name == "friends"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)
    assert field.type.of_type.of_type.of_type.of_type is str


def test_error_type_with_optional_field():
    class UserModel(pydantic.BaseModel):
        age: Optional[int]

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition
    assert definition.name == "UserError"

    [field] = definition.fields

    assert field.graphql_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert field.type.of_type.of_type is str


def test_error_type_with_list_of_optional_scalar():
    class UserModel(pydantic.BaseModel):
        age: List[Optional[int]]

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.graphql_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)
    assert field.type.of_type.of_type.of_type.of_type is str


def test_error_type_with_optional_list_scalar():
    class UserModel(pydantic.BaseModel):
        age: Optional[List[int]]

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.graphql_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)
    assert field.type.of_type.of_type.of_type.of_type is str


def test_error_type_with_optional_list_of_optional_scalar():
    class UserModel(pydantic.BaseModel):
        age: Optional[List[Optional[int]]]

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.graphql_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)
    assert field.type.of_type.of_type.of_type.of_type is str


def test_error_type_with_optional_list_of_nested_model():
    class FriendModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.error_type(FriendModel, fields=["name"])
    class FriendError(pydantic.BaseModel):
        pass

    class UserModel(pydantic.BaseModel):
        friends: Optional[List[FriendModel]]

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["friends"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.graphql_name == "friends"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert field.type.of_type.of_type.of_type is FriendError


def test_error_type_with_matrix_list_of_scalar():
    class UserModel(pydantic.BaseModel):
        age: List[List[int]]

    @strawberry.experimental.pydantic.error_type(UserModel, fields=["age"])
    class UserError:
        pass

    definition: TypeDefinition = UserError._type_definition

    assert definition.name == "UserError"
    [field] = definition.fields

    assert field.graphql_name == "age"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)

    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type, StrawberryList)

    assert isinstance(field.type.of_type.of_type.of_type.of_type, StrawberryOptional)
    assert isinstance(field.type.of_type.of_type.of_type.of_type.of_type,
                      StrawberryList)

    assert field.type.of_type.of_type.of_type.of_type.of_type.of_type is str
