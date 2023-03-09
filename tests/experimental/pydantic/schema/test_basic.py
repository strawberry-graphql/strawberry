import textwrap
from enum import Enum
from typing import List, Optional, Union

import pydantic

import strawberry


def test_basic_type_field_list():
    class UserModel(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel, fields=["age", "password"])
    class User:
        pass

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


def test_all_fields():
    class UserModel(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel, all_fields=True)
    class User:
        pass

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


def test_auto_fields():
    class UserModel(pydantic.BaseModel):
        age: int
        password: Optional[str]
        other: float

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age: strawberry.auto
        password: strawberry.auto

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
    class UserModel(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel, fields=["age_", "password"])
    class User:
        pass

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
    class UserModel(pydantic.BaseModel):
        age: int
        friend_names: List[str]

    @strawberry.experimental.pydantic.type(UserModel, fields=["age", "friend_names"])
    class User:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(age=1, friend_names=["A", "B"])

    schema = strawberry.Schema(query=Query)

    query = "{ user { friendNames } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["friendNames"] == ["A", "B"]


def test_basic_type_with_nested_model():
    class Hobby(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(Hobby, fields=["name"])
    class HobbyType:
        pass

    class User(pydantic.BaseModel):
        hobby: Hobby

    @strawberry.experimental.pydantic.type(User, fields=["hobby"])
    class UserType:
        pass

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
    class Hobby(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(Hobby, fields=["name"])
    class HobbyType:
        pass

    class User(pydantic.BaseModel):
        hobbies: List[Hobby]

    @strawberry.experimental.pydantic.type(User, fields=["hobbies"])
    class UserType:
        pass

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


def test_basic_type_with_extended_fields():
    class UserModel(pydantic.BaseModel):
        age: int

    @strawberry.experimental.pydantic.type(UserModel, fields=["age"])
    class User:
        name: str

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="Marco", age=100)

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    type Query {
      user: User!
    }

    type User {
      name: String!
      age: Int!
    }
    """
    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { name age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["name"] == "Marco"
    assert result.data["user"]["age"] == 100


def test_type_with_custom_resolver():
    class UserModel(pydantic.BaseModel):
        age: int

    def get_age_in_months(root):
        return root.age * 12

    @strawberry.experimental.pydantic.type(UserModel, fields=["age"])
    class User:
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
    class BranchA(pydantic.BaseModel):
        field_a: str

    class BranchB(pydantic.BaseModel):
        field_b: int

    class User(pydantic.BaseModel):
        union_field: Union[BranchA, BranchB]

    @strawberry.experimental.pydantic.type(BranchA, fields=["field_a"])
    class BranchAType:
        pass

    @strawberry.experimental.pydantic.type(BranchB, fields=["field_b"])
    class BranchBType:
        pass

    @strawberry.experimental.pydantic.type(User, fields=["union_field"])
    class UserType:
        pass

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


def test_basic_type_with_union_pydantic_types():
    class BranchA(pydantic.BaseModel):
        field_a: str

    class BranchB(pydantic.BaseModel):
        field_b: int

    class User(pydantic.BaseModel):
        union_field: Union[BranchA, BranchB]

    @strawberry.experimental.pydantic.type(BranchA, fields=["field_a"])
    class BranchAType:
        pass

    @strawberry.experimental.pydantic.type(BranchB, fields=["field_b"])
    class BranchBType:
        pass

    @strawberry.experimental.pydantic.type(User, fields=["union_field"])
    class UserType:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            # note that BranchB is a pydantic type, not a strawberry type
            return UserType(union_field=BranchB(field_b=10))

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

    class User(pydantic.BaseModel):
        age: int
        kind: UserKind

    @strawberry.experimental.pydantic.type(User, fields=["age", "kind"])
    class UserType:
        pass

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
    class Base(pydantic.BaseModel):
        base_field: str

    class BranchA(Base):
        field_a: str

    class BranchB(Base):
        field_b: int

    class User(pydantic.BaseModel):
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

    @strawberry.experimental.pydantic.type(User, fields=["interface_field"])
    class UserType:
        pass

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
