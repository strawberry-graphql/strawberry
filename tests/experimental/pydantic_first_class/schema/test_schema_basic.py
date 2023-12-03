import textwrap
from enum import Enum
from typing import List, Optional, Union

import pydantic
import pytest

import strawberry
from strawberry.experimental.pydantic.pydantic_first_class import first_class


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


def test_basic_alias_type():
    @first_class()
    class User(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
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


def test_basic_type_with_list():
    @first_class()
    class User(pydantic.BaseModel):
        age: int
        friend_names: List[str]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(age=1, friend_names=["A", "B"])

    schema = strawberry.Schema(
        query=Query,
    )

    query = "{ user { friendNames } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["friendNames"] == ["A", "B"]


def test_basic_type_with_nested_model():
    @first_class()
    class HobbyType(pydantic.BaseModel):
        name: str

    @first_class()
    class UserType(pydantic.BaseModel):
        hobby: HobbyType

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(hobby=HobbyType(name="Skii"))

    schema = strawberry.Schema(query=Query)

    query = "{ user { hobby { name } } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["hobby"]["name"] == "Skii"


def test_basic_type_with_list_of_nested_model():
    @first_class()
    class HobbyType(pydantic.BaseModel):
        name: str

    @first_class()
    class UserType(pydantic.BaseModel):
        hobbies: List[HobbyType]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(
                hobbies=[
                    HobbyType(name="Skii"),
                    HobbyType(name="Cooking"),
                ]
            )

    schema = strawberry.Schema(query=Query)

    query = "{ user { hobbies { name } } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["hobbies"] == [
        {"name": "Skii"},
        {"name": "Cooking"},
    ]


@pytest.mark.xfail(reason="No support for resolvers yet")
def test_type_with_custom_resolver():
    def get_age_in_months(root):
        return root.age * 12

    @first_class()
    class User(pydantic.BaseModel):
        age: int
        age_in_months: int = strawberry.field(resolver=get_age_in_months)

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(age=20)

    schema = strawberry.Schema(query=Query)

    query = "{ user { age ageInMonths } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 20
    assert result.data["user"]["ageInMonths"] == 240


def test_basic_type_with_union():
    @first_class()
    class BranchAType(pydantic.BaseModel):
        field_a: str

    @first_class()
    class BranchBType(pydantic.BaseModel):
        field_b: int

    @first_class()
    class UserType(pydantic.BaseModel):
        union_field: Union[BranchAType, BranchBType]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(union_field=BranchBType(field_b=10))

    schema = strawberry.Schema(query=Query)

    query = "{ user { unionField { ... on BranchBType { fieldB } } } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["unionField"]["fieldB"] == 10


def test_basic_type_with_enum():
    @strawberry.enum
    class UserKind(Enum):
        user = 0
        admin = 1

    @first_class()
    class UserType(pydantic.BaseModel):
        age: int
        kind: UserKind

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(age=10, kind=UserKind.admin)

    schema = strawberry.Schema(query=Query)

    query = "{ user { kind } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["kind"] == "admin"


def test_basic_type_with_interface():
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
        interface_field: BaseType

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(interface_field=BranchBType(base_field="abc", field_b=10))

    schema = strawberry.Schema(query=Query, types=[BranchAType, BranchBType])

    query = "{ user { interfaceField { baseField, ... on BranchBType { fieldB } } } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["interfaceField"]["baseField"] == "abc"
    assert result.data["user"]["interfaceField"]["fieldB"] == 10


def test_basic_type_with_optional_and_default():
    @first_class()
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str] = pydantic.Field(default="ABC")

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(age=1)

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

    query = "{ user { age password } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1
    assert result.data["user"]["password"] == "ABC"

    @strawberry.type
    class QueryNone:
        @strawberry.field
        def user(self) -> User:
            return User(age=1, password=None)

    schema = strawberry.Schema(query=QueryNone)

    query = "{ user { age password } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1
    assert result.data["user"]["password"] is None
