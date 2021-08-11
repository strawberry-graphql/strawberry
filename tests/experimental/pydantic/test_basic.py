from typing import List, Optional

import pytest

import pydantic

import strawberry
from strawberry.experimental.pydantic.exceptions import MissingFieldsListError
from strawberry.type import StrawberryList, StrawberryOptional
from strawberry.types.types import TypeDefinition


def test_basic_type():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User, fields=["age", "password"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.graphql_name is None
    assert field1.type is int

    assert field2.python_name == "password"
    assert field2.graphql_name is None
    assert isinstance(field2.resolved_type, StrawberryOptional)
    assert field2.type.of_type is str


def test_referencing_other_models_fails_when_not_registered():
    class Group(pydantic.BaseModel):
        name: str

    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        group: Group

    with pytest.raises(
        strawberry.experimental.pydantic.UnregisteredTypeException,
        match=("Cannot find a Strawberry Type for (.*) did you forget to register it?"),
    ):

        @strawberry.experimental.pydantic.type(
            User, fields=["age", "password", "group"]
        )
        class UserType:
            pass


def test_referencing_other_registered_models():
    class Group(pydantic.BaseModel):
        name: str

    class User(pydantic.BaseModel):
        age: int
        group: Group

    @strawberry.experimental.pydantic.type(Group, fields=["name"])
    class GroupType:
        pass

    @strawberry.experimental.pydantic.type(User, fields=["age", "group"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "group"
    assert field2.type is GroupType


def test_list():
    class User(pydantic.BaseModel):
        friend_names: List[str]

    @strawberry.experimental.pydantic.type(User, fields=["friend_names"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field] = definition.fields

    assert field.python_name == "friend_names"
    assert isinstance(field.resolved_type, StrawberryList)
    assert field.type.of_type is str


def test_list_of_types():
    class Friend(pydantic.BaseModel):
        name: str

    class User(pydantic.BaseModel):
        friends: Optional[List[Optional[Friend]]]

    @strawberry.experimental.pydantic.type(Friend, fields=["name"])
    class FriendType:
        pass

    @strawberry.experimental.pydantic.type(User, fields=["friends"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field] = definition.fields

    assert field.python_name == "friends"
    assert isinstance(field.resolved_type, StrawberryOptional)
    assert isinstance(field.resolved_type.of_type, StrawberryList)
    assert isinstance(field.resolved_type.of_type.of_type, StrawberryOptional)
    assert field.resolved_type.of_type.of_type.of_type is FriendType


def test_basic_type_without_fields_throws_an_error():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    with pytest.raises(MissingFieldsListError):

        @strawberry.experimental.pydantic.type(
            User,
            fields=[],
        )
        class UserType:
            pass


def test_type_with_fields_coming_from_strawberry_and_pydantic():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User, fields=["age", "password"])
    class UserType:
        name: str

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2, field3] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "name"
    assert field2.type is str

    assert field3.python_name == "password"
    assert isinstance(field3.resolved_type, StrawberryOptional)
    assert field3.resolved_type.of_type is str


@pytest.mark.xfail(
    reason=(
        "passing default values when extending types from pydantic is not"
        "supported. https://github.com/strawberry-graphql/strawberry/issues/829"
    )
)
def test_type_with_fields_coming_from_strawberry_and_pydantic_with_default():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User, fields=["age", "password"])
    class UserType:
        name: str = "Michael"

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2, field3] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "password"
    assert isinstance(field2.resolved_type, StrawberryOptional)
    assert field2.resolved_type.of_type is str

    assert field3.python_name == "name"
    assert field3.type is str
    assert field3.default == "Michael"


def test_type_with_nested_fields_coming_from_strawberry_and_pydantic():
    @strawberry.type
    class Name:
        first_name: str
        last_name: str

    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User, fields=["age", "password"])
    class UserType:
        name: Name

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2, field3] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "name"
    assert field2.type is Name

    assert field3.python_name == "password"
    assert isinstance(field3.resolved_type, StrawberryOptional)
    assert field3.resolved_type.of_type is str


def test_type_with_aliased_pydantic_field():
    class UserModel(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel, fields=["age_", "password"])
    class User:
        pass

    definition: TypeDefinition = User._type_definition
    assert definition.name == "User"

    [field1, field2] = definition.fields

    assert field1.python_name == "age_"
    assert field1.type is int

    assert field2.python_name == "password"
    assert isinstance(field2.resolved_type, StrawberryOptional)
    assert field2.resolved_type.of_type is str
