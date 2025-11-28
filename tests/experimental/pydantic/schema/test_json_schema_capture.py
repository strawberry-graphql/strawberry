import textwrap
from typing import Annotated, Optional, Union

import pydantic

import strawberry
from strawberry.schema_directive import Location
from tests.experimental.pydantic.utils import needs_pydantic_v2


def test_basic_type_field_list():
    class UserModel(pydantic.BaseModel):
        age: Annotated[int, pydantic.Field(gt=0, json_schema_extra={"test": 0})]
        password: pydantic.json_schema.SkipJsonSchema[Optional[str]]

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class JsonSchema:
        test: int
        exclusive_minimum: Optional[int] = None

    @strawberry.experimental.pydantic.type(UserModel, json_schema_directive=JsonSchema)
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
    directive @jsonSchema(test: Int!, exclusiveMinimum: Int = null) on FIELD_DEFINITION

    type Query {
      user: User!
    }

    type User {
      age: Int! @jsonSchema(test: 0, exclusiveMinimum: 0)
      password: String
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1


@needs_pydantic_v2
def test_can_use_both_pydantic_1_and_2():
    import pydantic
    from pydantic import v1 as pydantic_v1

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class JsonSchema:
        minimum: Optional[int] = None

    class UserModel(pydantic.BaseModel):
        age: Annotated[int, pydantic.Field(ge=0)]
        name: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel, json_schema_directive=JsonSchema)
    class User:
        age: strawberry.auto
        name: strawberry.auto

    class LegacyUserModel(pydantic_v1.BaseModel):
        age: int
        name: Optional[str]
        int_field: pydantic.v1.NonNegativeInt = 1

    @strawberry.experimental.pydantic.type(
        LegacyUserModel, json_schema_directive=JsonSchema
    )
    class LegacyUser:
        age: strawberry.auto
        name: strawberry.auto
        int_field: strawberry.auto

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, id: strawberry.ID) -> Union[User, LegacyUser]:
            if id == "legacy":
                return LegacyUser(age=1, name="legacy")

            return User(age=1, name="ABC")

    schema = strawberry.Schema(query=Query)

    expected_schema = """
    directive @jsonSchema(minimum: Int = null) on FIELD_DEFINITION

    type LegacyUser {
      age: Int!
      name: String
      intField: Int! @jsonSchema(minimum: 0)
    }

    type Query {
      user(id: ID!): UserLegacyUser!
    }

    type User {
      age: Int! @jsonSchema(minimum: 0)
      name: String
    }

    union UserLegacyUser = User | LegacyUser
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = """
        query ($id: ID!) {
            user(id: $id) {
                __typename
                ... on User { name }
                ... on LegacyUser { name }
            }
        }
    """

    result = schema.execute_sync(query, variable_values={"id": "new"})

    assert not result.errors
    assert result.data == {"user": {"__typename": "User", "name": "ABC"}}

    result = schema.execute_sync(query, variable_values={"id": "legacy"})

    assert not result.errors
    assert result.data == {"user": {"__typename": "LegacyUser", "name": "legacy"}}


def test_basic_with_alias_without_using_them():
    class UserModel(pydantic.BaseModel):
        age: Annotated[
            int, pydantic.Field(gt=0, json_schema_extra={"test": 0}, alias="userAge")
        ]
        password: pydantic.json_schema.SkipJsonSchema[Optional[str]]

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class JsonSchema:
        test: int
        exclusive_minimum: Optional[int] = None

    @strawberry.experimental.pydantic.type(
        UserModel, json_schema_directive=JsonSchema, use_pydantic_alias=False
    )
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
    directive @jsonSchema(test: Int!, exclusiveMinimum: Int = null) on FIELD_DEFINITION

    type Query {
      user: User!
    }

    type User {
      age: Int! @jsonSchema(test: 0, exclusiveMinimum: 0)
      password: String
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { age } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["age"] == 1


def test_basic_with_alias_and_use_them():
    class UserModel(pydantic.BaseModel):
        age: Annotated[
            int, pydantic.Field(gt=0, json_schema_extra={"test": 0}, alias="userAge")
        ]
        password: pydantic.json_schema.SkipJsonSchema[Optional[str]]

    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class JsonSchema:
        test: int
        exclusive_minimum: Optional[int] = None

    @strawberry.experimental.pydantic.type(
        UserModel, json_schema_directive=JsonSchema, use_pydantic_alias=True
    )
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
    directive @jsonSchema(test: Int!, exclusiveMinimum: Int = null) on FIELD_DEFINITION

    type Query {
      user: User!
    }

    type User {
      userAge: Int! @jsonSchema(test: 0, exclusiveMinimum: 0)
      password: String
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { userAge } }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data["user"]["userAge"] == 1
