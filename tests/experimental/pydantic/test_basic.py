from enum import Enum
from typing import List, Optional, Union

import pytest

import pydantic

import strawberry
from strawberry.enum import EnumDefinition
from strawberry.experimental.pydantic.exceptions import MissingFieldsListError
from strawberry.type import StrawberryList, StrawberryOptional
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion


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
    assert isinstance(field2.type, StrawberryOptional)
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
    assert isinstance(field.type, StrawberryList)
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
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert field.type.of_type.of_type.of_type is FriendType


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
    assert isinstance(field3.type, StrawberryOptional)
    assert field3.type.of_type is str


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
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is str

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
    assert isinstance(field3.type, StrawberryOptional)
    assert field3.type.of_type is str


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
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is str


def test_union():
    class BranchA(pydantic.BaseModel):
        field_a: str

    class BranchB(pydantic.BaseModel):
        field_b: int

    class User(pydantic.BaseModel):
        age: int
        union_field: Union[BranchA, BranchB]

    @strawberry.experimental.pydantic.type(BranchA, fields=["field_a"])
    class BranchAType:
        pass

    @strawberry.experimental.pydantic.type(BranchB, fields=["field_b"])
    class BranchBType:
        pass

    @strawberry.experimental.pydantic.type(User, fields=["age", "union_field"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "union_field"
    assert isinstance(field2.type, StrawberryUnion)
    assert field2.type.types[0] is BranchAType
    assert field2.type.types[1] is BranchBType


def test_enum():
    @strawberry.enum
    class UserKind(Enum):
        user = 0
        admin = 1

    class User(pydantic.BaseModel):
        age: int
        kind: UserKind

    @strawberry.experimental.pydantic.type(User, fields=["age", "kind"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "kind"
    assert isinstance(field2.type, EnumDefinition)
    assert field2.type.wrapped_cls is UserKind


def test_interface():
    class Base(pydantic.BaseModel):
        base_field: str

    class BranchA(Base):
        field_a: str

    class BranchB(Base):
        field_b: int

    class User(pydantic.BaseModel):
        age: int
        interface_field: Base

    @strawberry.experimental.pydantic.interface(Base, fields=["base_field"])
    class BaseType:
        pass

    @strawberry.experimental.pydantic.type(BranchA, fields=["field_a"])
    class BranchAType(BaseType):
        pass

    @strawberry.experimental.pydantic.type(BranchB, fields=["field_b"])
    class BranchBType(BaseType):
        pass

    @strawberry.experimental.pydantic.type(User, fields=["age", "interface_field"])
    class UserType:
        pass

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "interface_field"
    assert field2.type is BaseType
