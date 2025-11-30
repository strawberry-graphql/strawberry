# type: ignore
import dataclasses
import re
from enum import Enum
from typing import Annotated, Optional, TypeVar

import pytest

import strawberry
from strawberry.exceptions import MultipleStrawberryFieldsError
from strawberry.types.base import get_object_definition, has_object_definition
from strawberry.types.field import StrawberryField


def test_enum():
    @strawberry.enum
    class Count(Enum):
        TWO = "two"
        FOUR = "four"

    @strawberry.type
    class Animal:
        legs: Count

    field: StrawberryField = get_object_definition(Animal).fields[0]

    # TODO: Remove reference to .__strawberry_definition__ with StrawberryEnumDefinition
    assert field.type is Count.__strawberry_definition__


def test_forward_reference():
    global FromTheFuture

    @strawberry.type
    class TimeTraveler:
        origin: "FromTheFuture"

    @strawberry.type
    class FromTheFuture:
        year: int

    field: StrawberryField = get_object_definition(TimeTraveler).fields[0]

    assert field.type is FromTheFuture

    del FromTheFuture


def test_list():
    @strawberry.type
    class Santa:
        making_a: list[str]

    field: StrawberryField = get_object_definition(Santa).fields[0]

    assert field.type == list[str]


def test_literal():
    @strawberry.type
    class Fabric:
        thread_type: str

    field: StrawberryField = get_object_definition(Fabric).fields[0]

    assert field.type is str


def test_object():
    @strawberry.type
    class Object:
        proper_noun: bool

    @strawberry.type
    class TransitiveVerb:
        subject: Object

    field: StrawberryField = get_object_definition(TransitiveVerb).fields[0]

    assert field.type is Object


def test_optional():
    @strawberry.type
    class HasChoices:
        decision: bool | None

    field: StrawberryField = get_object_definition(HasChoices).fields[0]

    assert field.type == Optional[bool]


def test_type_var():
    T = TypeVar("T")

    @strawberry.type
    class Gossip:
        spill_the: T

    field: StrawberryField = get_object_definition(Gossip).fields[0]

    assert field.type == T


def test_union():
    @strawberry.type
    class Europe:
        name: str

    @strawberry.type
    class UK:
        name: str

    EU = Annotated[Europe | UK, strawberry.union("EU")]

    @strawberry.type
    class WishfulThinking:
        desire: EU

    field: StrawberryField = get_object_definition(WishfulThinking).fields[0]

    assert field.type == EU


def test_fields_with_defaults():
    @strawberry.type
    class Country:
        name: str = "United Kingdom"
        currency_code: str

    country = Country(currency_code="GBP")
    assert country.name == "United Kingdom"
    assert country.currency_code == "GBP"

    country = Country(name="United States of America", currency_code="USD")
    assert country.name == "United States of America"
    assert country.currency_code == "USD"


def test_fields_with_defaults_inheritance():
    @strawberry.interface
    class A:
        text: str
        delay: int | None = None

    @strawberry.type
    class B(A):
        attachments: list[A] | None = None

    @strawberry.type
    class C(A):
        fields: list[B]

    c_inst = C(
        text="some text",
        fields=[B(text="more text")],
    )

    assert dataclasses.asdict(c_inst) == {
        "text": "some text",
        "delay": None,
        "fields": [
            {
                "text": "more text",
                "attachments": None,
                "delay": None,
            }
        ],
    }


def test_positional_args_not_allowed():
    @strawberry.type
    class Thing:
        name: str

    with pytest.raises(
        TypeError,
        match=re.escape("__init__() takes 1 positional argument but 2 were given"),
    ):
        Thing("something")


def test_object_preserves_annotations():
    @strawberry.type
    class Object:
        a: bool
        b: Annotated[str, "something"]
        c: bool = strawberry.field(graphql_type=int)
        d: Annotated[str, "something"] = strawberry.field(graphql_type=int)

    assert Object.__annotations__ == {
        "a": bool,
        "b": Annotated[str, "something"],
        "c": bool,
        "d": Annotated[str, "something"],
    }


def test_has_object_definition_returns_true_for_object_type():
    @strawberry.type
    class Palette:
        name: str

    assert has_object_definition(Palette) is True


def test_has_object_definition_returns_false_for_enum():
    @strawberry.enum
    class Color(Enum):
        RED = "red"
        GREEN = "green"

    assert has_object_definition(Color) is False


def test_has_object_definition_returns_true_for_interface():
    @strawberry.interface
    class Node:
        id: str

    assert has_object_definition(Node) is True


def test_has_object_definition_returns_true_for_input():
    @strawberry.input
    class CreateUserInput:
        name: str

    assert has_object_definition(CreateUserInput) is True


def test_has_object_definition_returns_false_for_scalar():
    from strawberry.scalars import JSON

    assert has_object_definition(JSON) is False


def test_annotated_field_with_description():
    @strawberry.type
    class Query:
        name: Annotated[str, strawberry.field(description="The name")]

    definition = get_object_definition(Query)
    field = definition.fields[0]

    assert field.python_name == "name"
    assert field.description == "The name"
    assert field.type is str


def test_annotated_field_with_graphql_name():
    @strawberry.type
    class Query:
        name: Annotated[str, strawberry.field(name="fullName")]

    definition = get_object_definition(Query)
    field = definition.fields[0]

    assert field.python_name == "name"
    assert field.graphql_name == "fullName"
    assert field.type is str


def test_annotated_field_with_deprecation_reason():
    @strawberry.type
    class Query:
        name: Annotated[
            str, strawberry.field(deprecation_reason="Use fullName instead")
        ]

    definition = get_object_definition(Query)
    field = definition.fields[0]

    assert field.python_name == "name"
    assert field.deprecation_reason == "Use fullName instead"
    assert field.type is str


def test_annotated_field_optional():
    @strawberry.type
    class Query:
        name: Annotated[str | None, strawberry.field(description="Optional name")]

    definition = get_object_definition(Query)
    field = definition.fields[0]

    assert field.python_name == "name"
    assert field.description == "Optional name"
    assert field.type == Optional[str]


def test_annotated_field_with_default_value():
    @strawberry.type
    class Query:
        name: Annotated[str, strawberry.field(description="The name")] = "default"

    definition = get_object_definition(Query)
    field = definition.fields[0]

    assert field.python_name == "name"
    assert field.description == "The name"
    assert field.type is str

    query = Query()
    assert query.name == "default"


def test_annotated_field_with_list_type():
    @strawberry.type
    class Query:
        names: Annotated[list[str], strawberry.field(description="List of names")]

    definition = get_object_definition(Query)
    field = definition.fields[0]

    assert field.python_name == "names"
    assert field.description == "List of names"
    assert field.type == list[str]


def test_annotated_field_with_nested_type():
    @strawberry.type
    class Person:
        name: str

    @strawberry.type
    class Query:
        person: Annotated[Person, strawberry.field(description="A person")]

    definition = get_object_definition(Query)
    field = definition.fields[0]

    assert field.python_name == "person"
    assert field.description == "A person"
    assert field.type is Person


def test_annotated_field_with_metadata():
    @strawberry.type
    class Query:
        name: Annotated[
            str, strawberry.field(description="Name", metadata={"custom": "value"})
        ]

    definition = get_object_definition(Query)
    field = definition.fields[0]

    assert field.python_name == "name"
    assert field.description == "Name"
    assert field.metadata == {"custom": "value"}


@pytest.mark.raises_strawberry_exception(
    MultipleStrawberryFieldsError,
    match=(
        "Annotation for field `name` on type `Query` "
        "cannot have multiple `strawberry.field`s"
    ),
)
def test_annotated_field_multiple_raises_error():
    @strawberry.type
    class Query:
        name: Annotated[
            str,
            strawberry.field(description="First"),
            strawberry.field(description="Second"),
        ]


def test_annotated_field_with_other_annotations():
    """Test that Annotated with non-StrawberryField annotations still works."""

    @strawberry.type
    class Query:
        name: Annotated[str, "some metadata", 123]

    definition = get_object_definition(Query)
    field = definition.fields[0]

    assert field.python_name == "name"
    assert field.type is str


def test_annotated_field_mixed_with_regular_field():
    @strawberry.type
    class Query:
        annotated_field: Annotated[str, strawberry.field(description="Annotated")]
        regular_field: str = strawberry.field(description="Regular")
        plain_field: str

    definition = get_object_definition(Query)
    fields = {f.python_name: f for f in definition.fields}

    assert fields["annotated_field"].description == "Annotated"
    assert fields["regular_field"].description == "Regular"
    assert fields["plain_field"].description is None


def test_annotated_field_schema_generation():
    """Test that Annotated fields work correctly in schema generation."""

    @strawberry.type
    class Query:
        name: Annotated[str, strawberry.field(description="The name")]
        age: Annotated[int, strawberry.field(deprecation_reason="Use birthYear")]

    schema = strawberry.Schema(query=Query)
    schema_str = str(schema)

    assert '"The name"' in schema_str
    assert "@deprecated" in schema_str
    assert "Use birthYear" in schema_str


def test_annotated_field_with_input():
    """Test that Annotated fields work correctly with input types."""

    @strawberry.input
    class CreateUserInput:
        name: Annotated[str, strawberry.field(description="User's name")]
        email: Annotated[str, strawberry.field(description="User's email")]

    definition = get_object_definition(CreateUserInput)
    fields = {f.python_name: f for f in definition.fields}

    assert fields["name"].description == "User's name"
    assert fields["email"].description == "User's email"


def test_annotated_field_with_input_default_in_schema():
    """Test that Annotated fields with defaults show up correctly in schema."""

    @strawberry.input
    class CreateUserInput:
        name: Annotated[str, strawberry.field(description="User's name")] = "Anonymous"

    @strawberry.type
    class Query:
        @strawberry.field
        def create_user(self, input: CreateUserInput) -> str:
            return input.name

    schema = strawberry.Schema(query=Query)
    schema_str = str(schema)

    # The default value should appear in the GraphQL schema
    assert '= "Anonymous"' in schema_str
    assert "User's name" in schema_str

    # Instance should use the default
    instance = CreateUserInput()
    assert instance.name == "Anonymous"
