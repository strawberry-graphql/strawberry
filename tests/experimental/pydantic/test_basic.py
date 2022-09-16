import dataclasses
from enum import Enum
from typing import Any, List, Optional, Union

import pytest

import pydantic

import strawberry
from strawberry.enum import EnumDefinition
from strawberry.experimental.pydantic.exceptions import MissingFieldsListError
from strawberry.schema_directive import Location
from strawberry.type import StrawberryList, StrawberryOptional
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion


def test_basic_type_field_list():
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


def test_basic_type_all_fields():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User, all_fields=True)
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


@pytest.mark.filterwarnings("error")
def test_basic_type_all_fields_warn():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    with pytest.raises(
        UserWarning,
        match=("Using all_fields overrides any explicitly defined fields"),
    ):

        @strawberry.experimental.pydantic.type(User, all_fields=True)
        class UserType:
            age: strawberry.auto


def test_basic_type_auto_fields():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        other: float

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        password: strawberry.auto

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


def test_auto_fields_other_sentinel():
    class other_sentinel:
        pass

    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        other: int

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        password: strawberry.auto
        other: other_sentinel  # this should be a private field, not an auto field

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2, field3] = definition.fields

    assert field1.python_name == "age"
    assert field1.graphql_name is None
    assert field1.type is int

    assert field2.python_name == "password"
    assert field2.graphql_name is None
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is str

    assert field3.python_name == "other"
    assert field3.graphql_name is None
    assert field3.type is other_sentinel


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

        @strawberry.experimental.pydantic.type(User)
        class UserType:
            age: strawberry.auto
            password: strawberry.auto
            group: strawberry.auto


def test_referencing_other_input_models_fails_when_not_registered():
    class Group(pydantic.BaseModel):
        name: str

    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        group: Group

    @strawberry.experimental.pydantic.type(Group)
    class GroupType:
        name: strawberry.auto

    with pytest.raises(
        strawberry.experimental.pydantic.UnregisteredTypeException,
        match=("Cannot find a Strawberry Type for (.*) did you forget to register it?"),
    ):

        @strawberry.experimental.pydantic.input(User)
        class UserInputType:
            age: strawberry.auto
            password: strawberry.auto
            group: strawberry.auto


def test_referencing_other_registered_models():
    class Group(pydantic.BaseModel):
        name: str

    class User(pydantic.BaseModel):
        age: int
        group: Group

    @strawberry.experimental.pydantic.type(Group)
    class GroupType:
        name: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        group: strawberry.auto

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

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        friend_names: strawberry.auto

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

    @strawberry.experimental.pydantic.type(Friend)
    class FriendType:
        name: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        friends: strawberry.auto

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

        @strawberry.experimental.pydantic.type(User)
        class UserType:
            pass


def test_type_with_fields_coming_from_strawberry_and_pydantic():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        name: str
        age: strawberry.auto
        password: strawberry.auto

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2, field3] = definition.fields

    assert field1.python_name == "name"
    assert field1.type is str

    assert field2.python_name == "age"
    assert field2.type is int

    assert field3.python_name == "password"
    assert isinstance(field3.type, StrawberryOptional)
    assert field3.type.of_type is str


def test_default_and_default_factory():
    class User1(pydantic.BaseModel):
        friend: Optional[str] = "friend_value"

    @strawberry.experimental.pydantic.type(User1)
    class UserType1:
        friend: strawberry.auto

    assert UserType1().friend == "friend_value"
    assert UserType1().to_pydantic().friend == "friend_value"

    class User2(pydantic.BaseModel):
        friend: Optional[str] = None

    @strawberry.experimental.pydantic.type(User2)
    class UserType2:
        friend: strawberry.auto

    assert UserType2().friend is None
    assert UserType2().to_pydantic().friend is None

    # Test instantiation using default_factory

    class User3(pydantic.BaseModel):
        friend: Optional[str] = pydantic.Field(default_factory=lambda: "friend_value")

    @strawberry.experimental.pydantic.type(User3)
    class UserType3:
        friend: strawberry.auto

    assert UserType3().friend == "friend_value"
    assert UserType3().to_pydantic().friend == "friend_value"

    class User4(pydantic.BaseModel):
        friend: Optional[str] = pydantic.Field(default_factory=lambda: None)

    @strawberry.experimental.pydantic.type(User4)
    class UserType4:
        friend: strawberry.auto

    assert UserType4().friend is None
    assert UserType4().to_pydantic().friend is None


def test_type_with_fields_mutable_default():
    empty_list = []

    class User(pydantic.BaseModel):
        groups: List[str]
        friends: List[str] = empty_list

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        groups: strawberry.auto
        friends: strawberry.auto

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [groups_field, friends_field] = definition.fields

    assert groups_field.default is dataclasses.MISSING
    assert groups_field.default_factory is dataclasses.MISSING
    assert friends_field.default is dataclasses.MISSING

    # check that we really made a copy
    assert friends_field.default_factory() is not empty_list
    assert UserType(groups=["groups"]).friends is not empty_list
    UserType(groups=["groups"]).friends.append("joe")
    assert empty_list == []


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

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        name: str = "Michael"
        age: strawberry.auto
        password: strawberry.auto

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

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        name: Name
        age: strawberry.auto
        password: strawberry.auto

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2, field3] = definition.fields

    assert field1.python_name == "name"
    assert field1.type is Name

    assert field2.python_name == "age"
    assert field2.type is int

    assert field3.python_name == "password"
    assert isinstance(field3.type, StrawberryOptional)
    assert field3.type.of_type is str


def test_type_with_aliased_pydantic_field():
    class UserModel(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age_: strawberry.auto
        password: strawberry.auto

    definition: TypeDefinition = User._type_definition
    assert definition.name == "User"

    [field1, field2] = definition.fields

    assert field1.python_name == "age_"
    assert field1.type is int
    assert field1.graphql_name == "age"

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

    @strawberry.experimental.pydantic.type(BranchA)
    class BranchAType:
        field_a: strawberry.auto

    @strawberry.experimental.pydantic.type(BranchB)
    class BranchBType:
        field_b: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        union_field: strawberry.auto

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

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        kind: strawberry.auto

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

    @strawberry.experimental.pydantic.interface(Base)
    class BaseType:
        base_field: strawberry.auto

    @strawberry.experimental.pydantic.type(BranchA)
    class BranchAType(BaseType):
        field_a: strawberry.auto

    @strawberry.experimental.pydantic.type(BranchB)
    class BranchBType(BaseType):
        field_b: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        interface_field: strawberry.auto

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "interface_field"
    assert field2.type is BaseType


def test_both_output_and_input_type():
    class Work(pydantic.BaseModel):
        time: float

    class User(pydantic.BaseModel):
        name: str
        work: Optional[Work]

    class Group(pydantic.BaseModel):
        users: List[User]

    # Test both definition orders
    @strawberry.experimental.pydantic.input(Work)
    class WorkInput:
        time: strawberry.auto

    @strawberry.experimental.pydantic.type(Work)
    class WorkOutput:
        time: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserOutput:
        name: strawberry.auto
        work: strawberry.auto

    @strawberry.experimental.pydantic.input(User)
    class UserInput:
        name: strawberry.auto
        work: strawberry.auto

    @strawberry.experimental.pydantic.input(Group)
    class GroupInput:
        users: strawberry.auto

    @strawberry.experimental.pydantic.type(Group)
    class GroupOutput:
        users: strawberry.auto

    @strawberry.type
    class Query:
        groups: List[GroupOutput]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def updateGroup(group: GroupInput) -> GroupOutput:
            pass

    # This triggers the exception from #1504
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    expected_schema = """
input GroupInput {
  users: [UserInput!]!
}

type GroupOutput {
  users: [UserOutput!]!
}

type Mutation {
  updateGroup(group: GroupInput!): GroupOutput!
}

type Query {
  groups: [GroupOutput!]!
}

input UserInput {
  name: String!
  work: WorkInput = null
}

type UserOutput {
  name: String!
  work: WorkOutput
}

input WorkInput {
  time: Float!
}

type WorkOutput {
  time: Float!
}"""
    assert schema.as_str().strip() == expected_schema.strip()

    assert Group._strawberry_type == GroupOutput
    assert Group._strawberry_input_type == GroupInput
    assert User._strawberry_type == UserOutput
    assert User._strawberry_input_type == UserInput
    assert Work._strawberry_type == WorkOutput
    assert Work._strawberry_input_type == WorkInput


def test_single_field_changed_type():
    class User(pydantic.BaseModel):
        age: int

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: str

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1] = definition.fields

    assert field1.python_name == "age"
    assert field1.graphql_name is None
    assert field1.type is str


def test_type_with_aliased_pydantic_field_changed_type():
    class UserModel(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age_: str
        password: strawberry.auto

    definition: TypeDefinition = User._type_definition
    assert definition.name == "User"

    [field1, field2] = definition.fields

    assert field1.python_name == "age_"
    assert field1.type is str
    assert field1.graphql_name == "age"

    assert field2.python_name == "password"
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is str


def test_deprecated_fields():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        other: float

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto = strawberry.field(deprecation_reason="Because")
        password: strawberry.auto

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.graphql_name is None
    assert field1.type is int
    assert field1.deprecation_reason == "Because"

    assert field2.python_name == "password"
    assert field2.graphql_name is None
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is str


def test_permission_classes():
    class IsAuthenticated(strawberry.BasePermission):
        message = "User is not authenticated"

        def has_permission(
            self, source: Any, info: strawberry.types.Info, **kwargs
        ) -> bool:
            return False

    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        other: float

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto = strawberry.field(permission_classes=[IsAuthenticated])
        password: strawberry.auto

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.graphql_name is None
    assert field1.type is int
    assert field1.permission_classes == [IsAuthenticated]

    assert field2.python_name == "password"
    assert field2.graphql_name is None
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is str


def test_field_directives():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        reason: str

    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        other: float

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto = strawberry.field(directives=[Sensitive(reason="GDPR")])
        password: strawberry.auto

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.graphql_name is None
    assert field1.type is int
    assert field1.directives == [Sensitive(reason="GDPR")]

    assert field2.python_name == "password"
    assert field2.graphql_name is None
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is str


def test_alias_fields():
    class User(pydantic.BaseModel):
        age: int

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto = strawberry.field(name="ageAlias")

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    field1 = definition.fields[0]

    assert field1.python_name == "age"
    assert field1.graphql_name == "ageAlias"
    assert field1.type is int


def test_alias_fields_with_use_pydantic_alias():
    class User(pydantic.BaseModel):
        age: int
        state: str = pydantic.Field(alias="statePydantic")
        country: str = pydantic.Field(alias="countryPydantic")

    @strawberry.experimental.pydantic.type(User, use_pydantic_alias=True)
    class UserType:
        age: strawberry.auto = strawberry.field(name="ageAlias")
        state: strawberry.auto = strawberry.field(name="state")
        country: strawberry.auto

    definition: TypeDefinition = UserType._type_definition
    assert definition.name == "UserType"

    [field1, field2, field3] = definition.fields

    assert field1.python_name == "age"
    assert field1.graphql_name == "ageAlias"

    assert field2.python_name == "state"
    assert field2.graphql_name == "state"

    assert field3.python_name == "country"
    assert field3.graphql_name == "countryPydantic"
