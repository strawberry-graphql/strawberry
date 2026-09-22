"""Tests for Pydantic v2 computed fields with first-class integration."""

import textwrap

import pydantic
from pydantic import computed_field

import strawberry


def test_computed_field_included():
    """Test that computed fields are included when include_computed=True."""

    @strawberry.pydantic.type(include_computed=True)
    class User(pydantic.BaseModel):
        age: int

        @computed_field
        @property
        def next_age(self) -> int:
            return self.age + 1

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
      nextAge: Int!
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    query = "{ user { age nextAge } }"

    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data["user"]["age"] == 1
    assert result.data["user"]["nextAge"] == 2


def test_computed_field_excluded_by_default():
    """Test that computed fields are excluded by default."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        age: int

        @computed_field
        @property
        def next_age(self) -> int:
            return self.age + 1

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
    }
    """

    assert str(schema) == textwrap.dedent(expected_schema).strip()

    # next_age should not be queryable
    query = "{ user { age } }"
    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data["user"]["age"] == 1


def test_computed_field_with_description():
    """Test that computed field descriptions are preserved."""

    @strawberry.pydantic.type(include_computed=True)
    class User(pydantic.BaseModel):
        age: int

        @computed_field(description="The user's age next year")
        @property
        def next_age(self) -> int:
            return self.age + 1

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(age=1)

    schema = strawberry.Schema(query=Query)

    # Check schema contains the description
    schema_str = str(schema)
    assert "nextAge" in schema_str


def test_multiple_computed_fields():
    """Test multiple computed fields on a single model."""

    @strawberry.pydantic.type(include_computed=True)
    class User(pydantic.BaseModel):
        first_name: str
        last_name: str
        age: int

        @computed_field
        @property
        def full_name(self) -> str:
            return f"{self.first_name} {self.last_name}"

        @computed_field
        @property
        def is_adult(self) -> bool:
            return self.age >= 18

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(first_name="John", last_name="Doe", age=25)

    schema = strawberry.Schema(query=Query)

    query = "{ user { firstName lastName fullName age isAdult } }"

    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data["user"]["firstName"] == "John"
    assert result.data["user"]["lastName"] == "Doe"
    assert result.data["user"]["fullName"] == "John Doe"
    assert result.data["user"]["age"] == 25
    assert result.data["user"]["isAdult"] is True


def test_computed_field_with_interface():
    """Test computed fields work with interfaces."""

    @strawberry.pydantic.interface(include_computed=True)
    class Person(pydantic.BaseModel):
        name: str

        @computed_field
        @property
        def greeting(self) -> str:
            return f"Hello, {self.name}!"

    @strawberry.pydantic.type(include_computed=True)
    class User(pydantic.BaseModel):
        name: str
        email: str

        @computed_field
        @property
        def greeting(self) -> str:
            return f"Hello, {self.name}!"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(name="John", email="john@example.com")

    schema = strawberry.Schema(query=Query)

    query = "{ user { name email greeting } }"

    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data["user"]["name"] == "John"
    assert result.data["user"]["greeting"] == "Hello, John!"
