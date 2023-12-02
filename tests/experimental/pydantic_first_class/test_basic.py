import dataclasses
import sys
import textwrap
from enum import Enum
from typing import Annotated, Any, List, Optional, Union
from graphql import is_input_type

import pydantic
import pytest

import strawberry
from tests.experimental.pydantic.utils import needs_pydantic_v1

from strawberry.experimental.pydantic.first_class import (
    first_class,
)

from strawberry.types.types import StrawberryObjectDefinition

from strawberry.type import StrawberryList, StrawberryOptional

from strawberry.experimental.pydantic.exceptions import MissingFieldsListError

from strawberry.union import StrawberryUnion

from strawberry.enum import EnumDefinition

from strawberry.schema_directive import Location

from strawberry.experimental.pydantic.first_class import register_first_class


def test_basic_type_field_list():
    @first_class()
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(age=1, password="ABC")

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Query {
      user: User!
    }

    type User {
      age: Int!
      password: String
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1


def test_referencing_other_models_fails_when_not_registered():
    class Group(pydantic.BaseModel):
        name: str

    with pytest.raises(
        strawberry.experimental.pydantic.UnregisteredTypeException,
        match=("Cannot find a Strawberry Type for (.*) did you forget to register it?"),
    ):

        @first_class()
        class User(pydantic.BaseModel):
            age: int
            password: Optional[str]
            group: Group


def test_referencing_other_input_models_fails_when_not_registered():
    @first_class()  # Not an input type so it should fail
    class Group(pydantic.BaseModel):
        name: str

    with pytest.raises(
        strawberry.experimental.pydantic.UnregisteredTypeException,
        match=("Cannot find a Strawberry Type for (.*) did you forget to register it?"),
    ):

        @first_class(is_input=True)
        class User(pydantic.BaseModel):
            age: int
            password: Optional[str]
            group: Group


def test_referencing_other_registered_models():
    @first_class()
    class Group(pydantic.BaseModel):
        name: str

    @first_class()
    class User(pydantic.BaseModel):
        age: int
        group: Group

    definition: StrawberryObjectDefinition = User.__strawberry_definition__
    assert definition.name == "User"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "group"
    assert field2.type is Group


def test_list():
    @first_class()
    class User(pydantic.BaseModel):
        friend_names: List[str]

    definition: StrawberryObjectDefinition = User.__strawberry_definition__
    assert definition.name == "User"

    [field] = definition.fields

    assert field.python_name == "friend_names"
    assert isinstance(field.type, StrawberryList)
    assert field.type.of_type is str


def test_list_of_types():
    @first_class()
    class Friend(pydantic.BaseModel):
        name: str

    @first_class()
    class User(pydantic.BaseModel):
        friends: Optional[List[Optional[Friend]]]

    definition: StrawberryObjectDefinition = User.__strawberry_definition__
    assert definition.name == "User"

    [field] = definition.fields

    assert field.python_name == "friends"
    assert isinstance(field.type, StrawberryOptional)
    assert isinstance(field.type.of_type, StrawberryList)
    assert isinstance(field.type.of_type.of_type, StrawberryOptional)
    assert field.type.of_type.of_type.of_type is Friend


def test_optional_and_default():
    @first_class()
    class User(pydantic.BaseModel):
        age: int
        name: str = pydantic.Field("Michael", description="The user name")
        password: Optional[str] = pydantic.Field(default="ABC")
        passwordtwo: Optional[str] = None
        some_list: Optional[List[str]] = pydantic.Field(default_factory=list)
        check: Optional[bool] = False

    definition: StrawberryObjectDefinition = User.__strawberry_definition__
    assert definition.name == "User"

    [
        age_field,
        name_field,
        password_field,
        passwordtwo_field,
        some_list_field,
        check_field,
    ] = definition.fields

    assert age_field.python_name == "age"
    assert age_field.type is int

    assert name_field.python_name == "name"
    assert name_field.type is str

    assert password_field.python_name == "password"
    assert isinstance(password_field.type, StrawberryOptional)
    assert password_field.type.of_type is str

    assert passwordtwo_field.python_name == "passwordtwo"
    assert isinstance(passwordtwo_field.type, StrawberryOptional)
    assert passwordtwo_field.type.of_type is str

    assert some_list_field.python_name == "some_list"
    assert isinstance(some_list_field.type, StrawberryOptional)
    assert isinstance(some_list_field.type.of_type, StrawberryList)
    assert some_list_field.type.of_type.of_type is str

    assert check_field.python_name == "check"
    assert isinstance(check_field.type, StrawberryOptional)
    assert check_field.type.of_type is bool


def test_type_with_aliased_pydantic_field():
    @first_class()
    class User(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
        password: Optional[str]

    definition: StrawberryObjectDefinition = User.__strawberry_definition__
    assert definition.name == "User"

    [field1, field2] = definition.fields

    assert field1.python_name == "age_"
    assert field1.type is int
    assert field1.graphql_name == "age"

    assert field2.python_name == "password"
    assert isinstance(field2.type, StrawberryOptional)
    assert field2.type.of_type is str


def test_union():
    @first_class()
    class BranchAType(pydantic.BaseModel):
        field_a: str

    @first_class()
    class BranchBType(pydantic.BaseModel):
        field_b: int

    @first_class()
    class UserType(pydantic.BaseModel):
        age: int
        union_field: Union[BranchAType, BranchBType]

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
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

    @first_class()
    class UserType(pydantic.BaseModel):
        age: int
        kind: UserKind

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "kind"
    assert isinstance(field2.type, EnumDefinition)
    assert field2.type.wrapped_cls is UserKind


def test_interface():
    @first_class(is_interface=True)
    class BaseType(pydantic.BaseModel):
        base_field: str

    @first_class()
    class BranchAType(BaseType):
        field_a: str

    @first_class()
    class BranchBType(BaseType):
        field_b: int

    @first_class()
    class UserType(pydantic.BaseModel):
        age: int
        interface_field: BaseType

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "age"
    assert field1.type is int

    assert field2.python_name == "interface_field"
    assert field2.type is BaseType


# Excepted failure. Need to fix this. Currently fails because we now mutate the same
# __strawberry_definition__ field on the pydantic model. This is a problem because
# we need to be able to have both a) an input type and b) an output type on the
# same pydantic model. Maybe we need to have a separate __strawberry_input_definition__
# Or just store them in a dict rather than on the model itself.
@pytest.mark.xfail(reason="Need to fix this")
def test_both_output_and_input_type():
    @first_class(name="WorkInput", is_input=True)
    @first_class(name="WorkOutput")
    class Work(pydantic.BaseModel):
        time: float

    @first_class(name="UserInput", is_input=True)
    @first_class(name="UserOutput")
    class User(pydantic.BaseModel):
        name: str
        # Note that pydantic v2 requires an explicit default of None for Optionals
        work: Optional[Work] = None

    @first_class(name="GroupInput", is_input=True)
    @first_class(name="GroupOutput")
    class Group(pydantic.BaseModel):
        users: List[User]

    @strawberry.type
    class Query:
        groups: List[Group]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def updateGroup(group: Group) -> Group:
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


# No support yet for strawberry field in pydantic models
@pytest.mark.xfail(reason="Need to implement strawberry.field in pydantic models")
def test_deprecated_fields():
    @first_class()
    class UserType(pydantic.BaseModel):
        age: int = strawberry.field(deprecation_reason="Because")
        password: Optional[str]
        other: float

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
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


@pytest.mark.xfail(reason="Need to implement strawberry.field in pydantic models")
def test_permission_classes():
    class IsAuthenticated(strawberry.BasePermission):
        message = "User is not authenticated"

        def has_permission(
            self, source: Any, info: strawberry.types.Info, **kwargs: Any
        ) -> bool:
            return False

    @first_class()
    class UserType(pydantic.BaseModel):
        age: int = strawberry.field(permission_classes=[IsAuthenticated])
        password: Optional[str]
        other: float

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
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


@pytest.mark.xfail(reason="Need to implement strawberry.field in pydantic models")
def test_field_directives():
    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        reason: str

    @first_class()
    class UserType(pydantic.BaseModel):
        age: int = strawberry.field(directives=[Sensitive(reason="GDPR")])
        password: Optional[str]
        other: float

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
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


@pytest.mark.xfail(reason="Need to implement strawberry.field in pydantic models")
def test_alias_fields():
    class UserType(pydantic.BaseModel):
        age: int = strawberry.field(name="ageAlias")

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
    assert definition.name == "UserType"

    field1 = definition.fields[0]

    assert field1.python_name == "age"
    assert field1.graphql_name == "ageAlias"
    assert field1.type is int


@pytest.mark.xfail(reason="Need to implement strawberry.field in pydantic models")
def test_field_metadata():
    @first_class()
    class UserType(pydantic.BaseModel):
        private: bool
        public: bool

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
    assert definition.name == "UserType"

    [field1, field2] = definition.fields

    assert field1.python_name == "private"
    assert field1.metadata["admin_only"]

    assert field2.python_name == "public"
    assert not field2.metadata


def test_annotated():
    @first_class(is_input=True)
    class UserType(pydantic.BaseModel):
        a: Annotated[int, "metadata"]

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
    assert definition.name == "UserType"

    [field] = definition.fields
    assert field.python_name == "a"
    assert field.type is int


def test_nested_annotated():
    @first_class()
    class UserType(pydantic.BaseModel):
        a: Optional[Annotated[int, "metadata"]]
        b: Optional[List[Annotated[int, "metadata"]]]

    definition: StrawberryObjectDefinition = UserType.__strawberry_definition__
    assert definition.name == "UserType"

    [field_a, field_b] = definition.fields
    assert field_a.python_name == "a"
    assert isinstance(field_a.type, StrawberryOptional)
    assert field_a.type.of_type is int

    assert field_b.python_name == "b"
    assert isinstance(field_b.type, StrawberryOptional)
    assert isinstance(field_b.type.of_type, StrawberryList)
    assert field_b.type.of_type.of_type is int
