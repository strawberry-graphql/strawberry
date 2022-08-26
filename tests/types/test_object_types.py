# type: ignore
from enum import Enum
from typing import List, Optional, TypeVar

import strawberry
from strawberry.types.types import get_strawberry_definition


def test_enum():
    @strawberry.enum
    class Count(Enum):
        TWO = "two"
        FOUR = "four"

    @strawberry.type
    class Animal:
        legs: Count

    field = get_strawberry_definition(Animal).fields[0]

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

    field = get_strawberry_definition(TimeTraveler).fields[0]

    assert field.type is FromTheFuture

    del FromTheFuture


def test_list():
    @strawberry.type
    class Santa:
        making_a: List[str]

    field = get_strawberry_definition(Santa).fields[0]

    assert field.type == List[str]


def test_literal():
    @strawberry.type
    class Fabric:
        thread_type: str

    field = get_strawberry_definition(Fabric).fields[0]

    assert field.type == str


def test_object():
    @strawberry.type
    class Object:
        proper_noun: bool

    @strawberry.type
    class TransitiveVerb:
        subject: Object

    field = get_strawberry_definition(TransitiveVerb).fields[0]
    assert field.type is Object


def test_optional():
    @strawberry.type
    class HasChoices:
        decision: Optional[bool]

    field = get_strawberry_definition(HasChoices).fields[0]
    assert field.type == Optional[bool]


def test_type_var():
    T = TypeVar("T")

    @strawberry.type
    class Gossip:
        spill_the: T

    strawberry_definition = get_strawberry_definition(Gossip)
    field = strawberry_definition.fields[0]

    assert field.type == T


def test_union():
    @strawberry.type
    class Europe:
        name: str

    @strawberry.type
    class UK:
        name: str

    EU = strawberry.union("EU", types=(Europe, UK))

    @strawberry.type
    class WishfulThinking:
        desire: EU

    strawberry_definition = get_strawberry_definition(WishfulThinking)
    field = strawberry_definition.fields[0]

    assert field.type is EU
