import textwrap

import strawberry
from strawberry.printer import print_schema
from strawberry.schema.config import StrawberryConfig


def test_sort_schema_disabled_by_default():
    @strawberry.type
    class Query:
        zebra: str
        apple: str
        mango: str

    expected_type = """
    type Query {
      zebra: String!
      apple: String!
      mango: String!
    }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_enabled():
    @strawberry.type
    class Query:
        zebra: str
        apple: str
        mango: str

    expected_type = """
    type Query {
      apple: String!
      mango: String!
      zebra: String!
    }
    """

    schema = strawberry.Schema(query=Query, config=StrawberryConfig(sort_schema=True))

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_with_mutations():
    @strawberry.type
    class Query:
        user_by_name: str
        user_by_id: str
        user_by_email: str

    @strawberry.type
    class Mutation:
        update_user: str
        delete_user: str
        create_user: str

    expected_type = """
    type Mutation {
      createUser: String!
      deleteUser: String!
      updateUser: String!
    }

    type Query {
      userByEmail: String!
      userById: String!
      userByName: String!
    }
    """

    schema = strawberry.Schema(
        query=Query, mutation=Mutation, config=StrawberryConfig(sort_schema=True)
    )

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_with_multiple_types():
    @strawberry.type
    class User:
        username: str
        name: str
        email: str
        age: int

    @strawberry.type
    class Post:
        title: str
        author: User
        content: str

    @strawberry.type
    class Query:
        post: Post
        user: User

    expected_type = """
    type Post {
      author: User!
      content: String!
      title: String!
    }

    type Query {
      post: Post!
      user: User!
    }

    type User {
      age: Int!
      email: String!
      name: String!
      username: String!
    }
    """

    schema = strawberry.Schema(query=Query, config=StrawberryConfig(sort_schema=True))

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_with_interfaces():
    @strawberry.interface
    class Node:
        name: str
        id: strawberry.ID

    @strawberry.type
    class User(Node):
        username: str
        email: str

    @strawberry.type
    class Query:
        user: User

    expected_type = """
    interface Node {
      id: ID!
      name: String!
    }

    type Query {
      user: User!
    }

    type User implements Node {
      email: String!
      id: ID!
      name: String!
      username: String!
    }
    """

    schema = strawberry.Schema(query=Query, config=StrawberryConfig(sort_schema=True))

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_with_enums():
    from enum import Enum

    @strawberry.enum
    class Role(Enum):
        MODERATOR = "moderator"
        ADMIN = "admin"
        USER = "user"

    @strawberry.type
    class Query:
        role: Role

    expected_type = """
    type Query {
      role: Role!
    }

    enum Role {
      ADMIN
      MODERATOR
      USER
    }
    """

    schema = strawberry.Schema(query=Query, config=StrawberryConfig(sort_schema=True))

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_with_input_types():
    @strawberry.input
    class UserInput:
        username: str
        name: str
        email: str
        age: int

    @strawberry.type
    class Query:
        create_user: str = strawberry.field()

        @strawberry.field
        def search_users(self, input: UserInput) -> str:
            return "result"

    expected_type = """
    type Query {
      createUser: String!
      searchUsers(input: UserInput!): String!
    }

    input UserInput {
      age: Int!
      email: String!
      name: String!
      username: String!
    }
    """

    schema = strawberry.Schema(query=Query, config=StrawberryConfig(sort_schema=True))

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_with_unions():
    from typing import Union

    @strawberry.type
    class Cat:
        name: str

    @strawberry.type
    class Dog:
        name: str

    @strawberry.type
    class Query:
        animal: Union[Cat, Dog] = strawberry.field()

    expected_type = """
    type Cat {
      name: String!
    }

    union CatDog = Cat | Dog

    type Dog {
      name: String!
    }

    type Query {
      animal: CatDog!
    }
    """

    schema = strawberry.Schema(query=Query, config=StrawberryConfig(sort_schema=True))

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_preserves_functionality():
    @strawberry.type
    class Query:
        @strawberry.field
        def zebra(self) -> str:
            return "zebra_value"

        @strawberry.field
        def apple(self) -> str:
            return "apple_value"

        @strawberry.field
        def mango(self) -> str:
            return "mango_value"

    schema = strawberry.Schema(query=Query, config=StrawberryConfig(sort_schema=True))

    # Test that queries still work correctly
    result = schema.execute_sync("{ apple zebra mango }")
    assert result.errors is None
    assert result.data == {
        "apple": "apple_value",
        "zebra": "zebra_value",
        "mango": "mango_value",
    }


def test_sort_schema_with_camel_case():
    @strawberry.type
    class Query:
        user_by_name: str
        user_by_id: str
        user_by_email: str

    expected_type = """
    type Query {
      userByEmail: String!
      userById: String!
      userByName: String!
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(sort_schema=True, auto_camel_case=True)
    )

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_explicit_false():
    @strawberry.type
    class Query:
        zebra: str
        apple: str
        mango: str

    expected_type = """
    type Query {
      zebra: String!
      apple: String!
      mango: String!
    }
    """

    schema = strawberry.Schema(query=Query, config=StrawberryConfig(sort_schema=False))

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()


def test_sort_schema_with_subscriptions():
    from collections.abc import AsyncGenerator

    @strawberry.type
    class Query:
        hello: str

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def user_updated(self) -> AsyncGenerator[str, None]:
            yield "update"

        @strawberry.subscription
        async def count(self) -> AsyncGenerator[int, None]:
            yield 1

        @strawberry.subscription
        async def message_received(self) -> AsyncGenerator[str, None]:
            yield "message"

    expected_type = """
    type Query {
      hello: String!
    }

    type Subscription {
      count: Int!
      messageReceived: String!
      userUpdated: String!
    }
    """

    schema = strawberry.Schema(
        query=Query,
        subscription=Subscription,
        config=StrawberryConfig(sort_schema=True),
    )

    assert print_schema(schema) == textwrap.dedent(expected_type).strip()
