import textwrap
from typing import List, Optional

import pydantic

import strawberry


def test_basic_type():
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
      age: Int!
      name: String!
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
