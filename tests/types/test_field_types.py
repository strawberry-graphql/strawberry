from enum import Enum
from typing import List, Optional, TypeVar

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.field import StrawberryField
from strawberry.type import StrawberryList, StrawberryOptional
from strawberry.union import StrawberryUnion


def test_enum():
    @strawberry.enum
    class Egnum(Enum):
        a = "A"
        b = "B"

    field = StrawberryField()
    field.type = Egnum
    field.origin = test_enum

    # TODO: Remove reference to ._enum_definition with StrawberryEnum
    assert field.resolved_type is Egnum._enum_definition


def test_forward_reference():
    global RefForward

    field = StrawberryField()
    field.type = "RefForward"
    field.origin = test_forward_reference

    @strawberry.type
    class RefForward:
        ref: int

    assert field.resolved_type is RefForward

    del RefForward


def test_list():
    field = StrawberryField()
    field.type = List[int]
    field.origin = test_list

    assert field.type == List[int]
    assert isinstance(field.resolved_type, StrawberryList)
    assert field.resolved_type.of_type == int


def test_literal():
    field = StrawberryField()
    field.type = bool
    field.origin = test_literal

    assert field.type == bool
    assert field.resolved_type is bool


def test_object():
    @strawberry.type
    class TypeyType:
        value: str

    field = StrawberryField()
    field.type = TypeyType
    field.origin = test_object

    assert field.type == TypeyType
    assert field.resolved_type is TypeyType


def test_optional():
    field = StrawberryField()
    field.type = Optional[float]
    field.origin = test_optional

    assert field.type == Optional[float]
    assert isinstance(field.resolved_type, StrawberryOptional)
    assert field.resolved_type.of_type == float


def test_type_var():
    T = TypeVar("T")

    field = StrawberryField()
    field.type = T

    assert field.type == T


def test_union():
    @strawberry.type
    class Un:
        fi: int

    @strawberry.type
    class Ion:
        eld: float

    union = StrawberryUnion(
        name="UnionName",
        type_annotations=(StrawberryAnnotation(Un), StrawberryAnnotation(Ion)),
    )
    field = StrawberryField()
    field.type = union

    assert field.type is union
