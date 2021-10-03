from enum import Enum
from typing import List, Optional, TypeVar

import pytest

import strawberry
from strawberry.exceptions import NotAClass
from strawberry.field import StrawberryField


def test_enum():
    @strawberry.enum
    class Count(Enum):
        TWO = "two"
        FOUR = "four"

    @strawberry.type
    class Animal:
        legs: Count

    # TODO: Remove reference to ._type_definition with StrawberryObject
    field: StrawberryField = Animal._type_definition.fields[0]

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

    # TODO: Remove reference to ._type_definition with StrawberryObject
    field: StrawberryField = TimeTraveler._type_definition.fields[0]

    assert field.type is FromTheFuture

    del FromTheFuture


def test_list():
    @strawberry.type
    class Santa:
        making_a: List[str]

    # TODO: Remove reference to ._type_definition with StrawberryObject
    field: StrawberryField = Santa._type_definition.fields[0]

    assert field.type == List[str]


def test_literal():
    @strawberry.type
    class Fabric:
        thread_type: str

    # TODO: Remove reference to ._type_definition with StrawberryObject
    field: StrawberryField = Fabric._type_definition.fields[0]

    assert field.type == str


def test_object():
    @strawberry.type
    class Object:
        proper_noun: bool

    @strawberry.type
    class TransitiveVerb:
        subject: Object

    # TODO: Remove reference to ._type_definition with StrawberryObject
    field: StrawberryField = TransitiveVerb._type_definition.fields[0]

    assert field.type is Object


def test_optional():
    @strawberry.type
    class HasChoices:
        decision: Optional[bool]

    # TODO: Remove reference to ._type_definition with StrawberryObject
    field: StrawberryField = HasChoices._type_definition.fields[0]

    assert field.type == Optional[bool]


def test_type_var():
    T = TypeVar("T")

    @strawberry.type
    class Gossip:
        spill_the: T

    # TODO: Remove reference to ._type_definition with StrawberryObject
    field: StrawberryField = Gossip._type_definition.fields[0]

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

    # TODO: Remove reference to ._type_definition with StrawberryObject
    field: StrawberryField = WishfulThinking._type_definition.fields[0]

    assert field.type is EU


def test_raises_error_when_using_type_with_a_not_class_object():
    expected_error = "strawberry.type can only be used with classes"
    with pytest.raises(NotAClass, match=expected_error):

        @strawberry.type
        def not_a_class():
            pass


def test_raises_error_when_using_input_with_a_not_class_object():
    expected_error = "strawberry.input can only be used with classes"
    with pytest.raises(NotAClass, match=expected_error):

        @strawberry.input
        def not_a_class():
            pass


def test_raises_error_when_using_interface_with_a_not_class_object():
    expected_error = "strawberry.interface can only be used with classes"
    with pytest.raises(NotAClass, match=expected_error):

        @strawberry.interface
        def not_a_class():
            pass
