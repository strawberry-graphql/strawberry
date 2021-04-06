from typing import List, Optional

import pytest

import pydantic

import strawberry
from strawberry.experimental.pydantic.exceptions import MissingFieldsListError
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
    assert len(definition.fields) == 2

    assert definition.fields[0].graphql_name == "age"
    assert definition.fields[0].type is int
    assert definition.fields[0].is_optional is False

    assert definition.fields[1].graphql_name == "password"
    assert definition.fields[1].type is str
    assert definition.fields[1].is_optional is True


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
    assert len(definition.fields) == 2

    assert definition.fields[0].graphql_name == "age"
    assert definition.fields[0].type is int
    assert definition.fields[0].is_optional is False

    assert definition.fields[1].graphql_name == "group"
    assert definition.fields[1].type is GroupType


def test_list():
    class User(pydantic.BaseModel):
        friend_names: List[str]

    @strawberry.experimental.pydantic.type(User, fields=["friend_names"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition

    assert definition.name == "UserType"
    assert len(definition.fields) == 1

    assert definition.fields[0].graphql_name == "friendNames"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is False
    assert definition.fields[0].is_list is True
    assert definition.fields[0].child.type is str


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
    assert len(definition.fields) == 1

    assert definition.fields[0].graphql_name == "friends"
    assert definition.fields[0].type is None
    assert definition.fields[0].is_optional is True
    assert definition.fields[0].is_list is True
    assert definition.fields[0].child.type is FriendType
    assert definition.fields[0].child.is_optional is True


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
    assert len(definition.fields) == 3

    assert definition.fields[0].graphql_name == "age"
    assert definition.fields[0].type is int
    assert definition.fields[0].is_optional is False

    assert definition.fields[1].graphql_name == "password"
    assert definition.fields[1].type is str
    assert definition.fields[1].is_optional is True

    assert definition.fields[2].graphql_name == "name"
    assert definition.fields[2].type is str
    assert definition.fields[2].is_optional is False


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
    assert len(definition.fields) == 3

    assert definition.fields[0].graphql_name == "age"
    assert definition.fields[0].type is int
    assert definition.fields[0].is_optional is False

    assert definition.fields[1].graphql_name == "password"
    assert definition.fields[1].type is str
    assert definition.fields[1].is_optional is True

    assert definition.fields[2].graphql_name == "name"
    assert definition.fields[2].type is Name
    assert definition.fields[2].is_optional is False


def test_type_with_aliased_pydantic_field():
    class UserModel(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel, fields=["age_", "password"])
    class User:
        pass

    definition: TypeDefinition = User._type_definition

    assert definition.name == "User"
    assert len(definition.fields) == 2

    assert definition.fields[0].graphql_name == "age"
    assert definition.fields[0].type is int
    assert definition.fields[0].is_optional is False

    assert definition.fields[1].graphql_name == "password"
    assert definition.fields[1].type is str
    assert definition.fields[1].is_optional is True
