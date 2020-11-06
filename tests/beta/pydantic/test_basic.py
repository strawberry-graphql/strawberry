from typing import List, Optional

import pytest

import pydantic

import strawberry
from strawberry.beta.pydantic.exceptions import MissingFieldsListError
from strawberry.types.types import TypeDefinition


def test_basic_type():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.beta.pydantic.type(User, fields=["age", "password"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition

    assert definition.name == "UserType"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "age"
    assert definition.fields[0].type == int
    assert definition.fields[0].is_optional is False

    assert definition.fields[1].name == "password"
    assert definition.fields[1].type == str
    assert definition.fields[1].is_optional


def test_referencing_other_models_fails_when_not_registered():
    class Group(pydantic.BaseModel):
        name: str

    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        group: Group

    with pytest.raises(
        strawberry.beta.pydantic.UnregisteredTypeException,
        match=("Cannot find a Strawberry Type for (.*) did you forget to register it?"),
    ):

        @strawberry.beta.pydantic.type(User, fields=["age", "password", "group"])
        class UserType:
            pass


def test_referencing_other_registered_models():
    class Group(pydantic.BaseModel):
        name: str

    class User(pydantic.BaseModel):
        age: int
        group: Group

    @strawberry.beta.pydantic.type(Group, fields=["name"])
    class GroupType:
        pass

    @strawberry.beta.pydantic.type(User, fields=["age", "group"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition

    assert definition.name == "UserType"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "age"
    assert definition.fields[0].type == int
    assert definition.fields[0].is_optional is False

    assert definition.fields[1].name == "group"
    assert definition.fields[1].type == GroupType


def test_list():
    class User(pydantic.BaseModel):
        friend_names: List[str]

    @strawberry.beta.pydantic.type(User, fields=["friend_names"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition

    assert definition.name == "UserType"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "friendNames"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].is_list is True
    assert definition.fields[0].child.type == str


def test_list_of_types():
    class Friend(pydantic.BaseModel):
        name: str

    class User(pydantic.BaseModel):
        friends: Optional[List[Optional[Friend]]]

    @strawberry.beta.pydantic.type(Friend, fields=["name"])
    class FriendType:
        pass

    @strawberry.beta.pydantic.type(User, fields=["friends"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition

    assert definition.name == "UserType"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "friends"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is True
    assert definition.fields[0].is_list is True
    assert definition.fields[0].child.type == FriendType
    assert definition.fields[0].child.is_optional is True


def test_basic_type_without_fields_throws_an_error():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    with pytest.raises(MissingFieldsListError):

        @strawberry.beta.pydantic.type(
            User,
            fields=[],
        )
        class UserType:
            pass


def test_type_with_fields_coming_from_strawberry_and_pydantic():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.beta.pydantic.type(User, fields=["age", "password"])
    class UserType:
        name: str

    definition: TypeDefinition = UserType._type_definition

    assert definition.name == "UserType"
    assert len(definition.fields) == 3

    assert definition.fields[0].name == "age"
    assert definition.fields[0].type == int
    assert definition.fields[0].is_optional is False

    assert definition.fields[1].name == "password"
    assert definition.fields[1].type == str
    assert definition.fields[1].is_optional

    assert definition.fields[2].name == "name"
    assert definition.fields[2].type == str
    assert definition.fields[2].is_optional is False


def test_type_with_nested_fields_coming_from_strawberry_and_pydantic():
    @strawberry.type
    class Name:
        first_name: str
        last_name: str

    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.beta.pydantic.type(User, fields=["age", "password"])
    class UserType:
        name: Name

    definition: TypeDefinition = UserType._type_definition

    assert definition.name == "UserType"
    assert len(definition.fields) == 3

    assert definition.fields[0].name == "age"
    assert definition.fields[0].type == int
    assert definition.fields[0].is_optional is False

    assert definition.fields[1].name == "password"
    assert definition.fields[1].type == str
    assert definition.fields[1].is_optional

    assert definition.fields[2].name == "name"
    assert definition.fields[2].type == Name
    assert definition.fields[2].is_optional is False
