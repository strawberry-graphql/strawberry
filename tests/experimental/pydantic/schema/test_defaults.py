import textwrap
from typing import Optional

import pydantic

import strawberry
from strawberry.printer import print_schema
from tests.conftest import skip_if_gql_32
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


@skip_if_gql_32("formatting is different in gql 3.2")
def test_v2_input_with_nonscalar_default():
    class NonScalarType(pydantic.BaseModel):
        id: int = 10
        nullable_field: Optional[int] = None

    class Owning(pydantic.BaseModel):
        non_scalar_type: NonScalarType = NonScalarType()
        id: int = 10

    @strawberry.experimental.pydantic.type(
        model=NonScalarType, all_fields=True, is_input=True
    )
    class NonScalarTypeInput: ...

    @strawberry.experimental.pydantic.type(model=Owning, all_fields=True, is_input=True)
    class OwningInput: ...

    @strawberry.type
    class ExampleOutput:
        owning_id: int
        non_scalar_id: int
        non_scalar_nullable_field: Optional[int]

    @strawberry.type
    class Query:
        @strawberry.field()
        def test(self, x: OwningInput) -> ExampleOutput:
            return ExampleOutput(
                owning_id=x.id,
                non_scalar_id=x.non_scalar_type.id,
                non_scalar_nullable_field=x.non_scalar_type.nullable_field,
            )

    schema = strawberry.Schema(Query)

    expected = """
    type ExampleOutput {
      owningId: Int!
      nonScalarId: Int!
      nonScalarNullableField: Int
    }

    input NonScalarTypeInput {
      id: Int! = 10
      nullableField: Int = null
    }

    input OwningInput {
      nonScalarType: NonScalarTypeInput! = { id: 10 }
      id: Int! = 10
    }

    type Query {
      test(x: OwningInput!): ExampleOutput!
    }
    """

    assert print_schema(schema) == textwrap.dedent(expected).strip()

    query = """
    query($input_data: OwningInput!)
    {
        test(x: $input_data) {
            owningId nonScalarId nonScalarNullableField
        }
    }
    """
    result = schema.execute_sync(
        query, variable_values={"input_data": {"nonScalarType": {}}}
    )

    assert not result.errors
    expected_result = {
        "owningId": 10,
        "nonScalarId": 10,
        "nonScalarNullableField": None,
    }
    assert result.data["test"] == expected_result
