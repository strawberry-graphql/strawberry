# type: ignore
import dataclasses
import re
from enum import Enum
from typing import Annotated, Optional, TypeVar, Union

import pytest

import strawberry
from strawberry.types.base import get_object_definition
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

    # TODO: Remove reference to ._enum_definition with StrawberryEnum
    assert field.type is Count._enum_definition


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
        decision: Optional[bool]

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

    EU = Annotated[Union[Europe, UK], strawberry.union("EU")]

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
        delay: Optional[int] = None

    @strawberry.type
    class B(A):
        attachments: Optional[list[A]] = None

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
