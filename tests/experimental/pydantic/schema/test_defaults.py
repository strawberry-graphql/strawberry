import textwrap
from typing import Optional

import pydantic

import strawberry
from strawberry.printer import print_schema
from tests.experimental.pydantic.utils import needs_pydantic_v2


def test_field_type_default():
    class User(pydantic.BaseModel):
        name: str = "James"
        nickname: Optional[str] = "Jim"

    @strawberry.experimental.pydantic.type(User, all_fields=True)
    class PydanticUser: ...

    @strawberry.type
    class StrawberryUser:
        name: str = "James"

    @strawberry.type
    class Query:
        @strawberry.field
        def a(self) -> PydanticUser:
            return PydanticUser()

        @strawberry.field
        def b(self) -> StrawberryUser:
            return StrawberryUser()

    schema = strawberry.Schema(Query)

    # name should be required in both the PydanticUser and StrawberryUser
    expected = """
    type PydanticUser {
      name: String!
      nickname: String
    }

    type Query {
      a: PydanticUser!
      b: StrawberryUser!
    }

    type StrawberryUser {
      name: String!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()


def test_pydantic_type_default_none():
    class UserPydantic(pydantic.BaseModel):
        name: Optional[str] = None

    @strawberry.experimental.pydantic.type(UserPydantic, all_fields=True)
    class User: ...

    @strawberry.type
    class Query:
        a: User = strawberry.field()

        @strawberry.field
        def a(self) -> User:
            return User()

    schema = strawberry.Schema(Query)

    expected = """
    type Query {
      a: User!
    }

    type User {
      name: String
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()


def test_pydantic_type_no_default_but_optional():
    class UserPydantic(pydantic.BaseModel):
        # pydantic automatically adds a default of None for Optional fields
        name: Optional[str]

    @strawberry.experimental.pydantic.type(UserPydantic, all_fields=True)
    class User: ...

    @strawberry.type
    class Query:
        a: User = strawberry.field()

        @strawberry.field
        def a(self) -> User:
            return User()

    schema = strawberry.Schema(Query)

    expected = """
    type Query {
      a: User!
    }

    type User {
      name: String
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()


def test_input_type_default():
    class User(pydantic.BaseModel):
        name: str = "James"

    @strawberry.experimental.pydantic.type(User, all_fields=True, is_input=True)
    class PydanticUser: ...

    @strawberry.type(is_input=True)
    class StrawberryUser:
        name: str = "James"

    @strawberry.type
    class Query:
        @strawberry.field
        def a(self, user: PydanticUser) -> str:
            return user.name

        @strawberry.field
        def b(self, user: StrawberryUser) -> str:
            return user.name

    schema = strawberry.Schema(Query)

    # name should be required in both the PydanticUser and StrawberryUser
    expected = """
    input PydanticUser {
      name: String! = "James"
    }

    type Query {
      a(user: PydanticUser!): String!
      b(user: StrawberryUser!): String!
    }

    input StrawberryUser {
      name: String! = "James"
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()


@needs_pydantic_v2
def test_v2_explicit_default():
    class User(pydantic.BaseModel):
        name: Optional[str]

    @strawberry.experimental.pydantic.type(User, all_fields=True)
    class PydanticUser: ...

    @strawberry.type
    class Query:
        @strawberry.field
        def a(self) -> PydanticUser:
            raise NotImplementedError

    schema = strawberry.Schema(Query)

    # name should have no default
    expected = """
    type PydanticUser {
      name: String
    }

    type Query {
      a: PydanticUser!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()
