from typing import Optional

import pytest

import pydantic
import strawberry
from strawberry.types.types import TypeDefinition


def test_basic_type():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.pydantic.type(User)
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
        strawberry.pydantic.UnregisteredTypeException,
        match=("Cannot find a Strawberry Type for (.*) did you forget to register it?"),
    ):

        @strawberry.pydantic.type(User)
        class UserType:
            pass


def test_referencing_other_registered_models():
    class Group(pydantic.BaseModel):
        name: str

    class User(pydantic.BaseModel):
        age: int
        group: Group

    @strawberry.pydantic.type(Group)
    class GroupType:
        pass

    @strawberry.pydantic.type(User)
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
