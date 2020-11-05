from typing import List, Optional

import pydantic

import strawberry


def test_basic_type():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.beta.pydantic.type(User, fields=["age", "password"])
    class UserType:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(age=1, password="ABC")

    schema = strawberry.Schema(query=Query)

    query = "{ user { age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1


def test_basic_type_with_list():
    class User(pydantic.BaseModel):
        age: int
        friend_names: List[str]

    @strawberry.beta.pydantic.type(User, fields=["age", "friend_names"])
    class UserType:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> UserType:
            return UserType(age=1, friend_names=["A", "B"])

    schema = strawberry.Schema(query=Query)

    query = "{ user { friendNames } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["friendNames"] == ["A", "B"]


def test_basic_type_with_nested_model():
    class Hobby(pydantic.BaseModel):
        name: str

    @strawberry.beta.pydantic.type(Hobby, fields=["name"])
    class HobbyType:
        pass

    class User(pydantic.BaseModel):
        hobby: Hobby

    @strawberry.beta.pydantic.type(User, fields=["hobby"])
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

    @strawberry.beta.pydantic.type(Hobby, fields=["name"])
    class HobbyType:
        pass

    class User(pydantic.BaseModel):
        hobbies: List[Hobby]

    @strawberry.beta.pydantic.type(User, fields=["hobbies"])
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
