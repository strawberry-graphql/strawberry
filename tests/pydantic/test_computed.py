"""Tests for Pydantic v2 computed fields with first-class integration."""

import textwrap
from typing import Annotated, Any, Optional

import pydantic
from pydantic import computed_field

import strawberry
from strawberry.scalars import JSON
from strawberry.types.base import get_object_definition


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


def test_computed_fields_can_be_excluded():
    """Test that computed fields can be excluded with include_computed=False."""

    @strawberry.pydantic.type(include_computed=False)
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


def test_computed_fields_are_included_by_default():
    @strawberry.pydantic.type
    class Person(pydantic.BaseModel):
        first: str
        last: str

        @computed_field
        @property
        def full_name(self) -> str:
            return f"{self.first} {self.last}"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person(first="Ada", last="Lovelace")

    schema = strawberry.Schema(query=Query)

    assert "fullName: String!" in str(schema)

    result = schema.execute_sync("{ person { fullName } }")

    assert not result.errors
    assert result.data == {"person": {"fullName": "Ada Lovelace"}}


class IsAdmin(strawberry.BasePermission):
    message = "Admins only"

    def has_permission(self, source: Any, info: strawberry.Info, **kwargs: Any) -> bool:
        return False


def test_computed_fields_can_be_customized():
    @strawberry.pydantic.type
    class Account(pydantic.BaseModel):
        balance: int

        @computed_field
        @property
        def balance_label(
            self,
        ) -> Annotated[str, strawberry.field(permission_classes=[IsAdmin])]:
            return f"{self.balance} EUR"

        @computed_field
        @property
        def metadata(
            self,
        ) -> Annotated[dict[str, Any], strawberry.field(graphql_type=JSON)]:
            return {"currency": "EUR"}

        @computed_field
        @property
        def internal_score(self) -> strawberry.Private[int]:
            return 42

    @strawberry.type
    class Query:
        @strawberry.field
        def account(self) -> Account:
            return Account(balance=10)

    schema = strawberry.Schema(query=Query)

    assert "metadata: JSON!" in str(schema)
    assert "internalScore" not in str(schema)

    result = schema.execute_sync("{ account { metadata } }")

    assert not result.errors
    assert result.data == {"account": {"metadata": {"currency": "EUR"}}}

    result = schema.execute_sync("{ account { balanceLabel } }")

    assert result.errors
    assert result.errors[0].message == "Admins only"


def test_computed_fields_overridden_by_resolver_fields():
    class Base(pydantic.BaseModel):
        name: str

        @computed_field
        @property
        def display(self) -> str:
            return self.name

    @strawberry.pydantic.type
    class Child(Base):
        @strawberry.pydantic.field
        def display(self) -> int:  # type: ignore[override]
            return len(self.name)

    [display] = [
        field
        for field in get_object_definition(Child, strict=True).fields
        if field.python_name == "display"
    ]

    assert display.base_resolver is not None


@strawberry.pydantic.type
class Parent(pydantic.BaseModel):
    children: list["Child"] = []

    # the forward reference can't be resolved yet when the class is created
    @computed_field
    @property
    def first_child(self) -> Optional["Child"]:
        return self.children[0] if self.children else None


@strawberry.pydantic.type
class Child(pydantic.BaseModel):
    name: str


Parent.model_rebuild()


def test_computed_fields_with_forward_references():
    @strawberry.type
    class Query:
        @strawberry.field
        def parent(self) -> Parent:
            return Parent(children=[Child(name="Ada")])

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync("{ parent { firstChild { name } } }")

    assert not result.errors
    assert result.data == {"parent": {"firstChild": {"name": "Ada"}}}
