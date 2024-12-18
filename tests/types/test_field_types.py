from enum import Enum
from typing import Optional, TypeVar

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.types.field import StrawberryField
from strawberry.types.union import StrawberryUnion


def test_enum():
    @strawberry.enum
    class Egnum(Enum):
        a = "A"
        b = "B"

    annotation = StrawberryAnnotation(Egnum)
    field = StrawberryField(type_annotation=annotation)

    # TODO: Remove reference to ._enum_definition with StrawberryEnum
    assert field.type is Egnum._enum_definition


def test_forward_reference():
    global RefForward

    annotation = StrawberryAnnotation("RefForward", namespace=globals())
    field = StrawberryField(type_annotation=annotation)

    @strawberry.type
    class RefForward:
        ref: int

    assert field.type is RefForward

    del RefForward


def test_list():
    annotation = StrawberryAnnotation(list[int])
    field = StrawberryField(type_annotation=annotation)

    assert field.type == list[int]


def test_literal():
    annotation = StrawberryAnnotation(bool)
    field = StrawberryField(type_annotation=annotation)

    assert field.type is bool


def test_object():
    @strawberry.type
    class TypeyType:
        value: str

    annotation = StrawberryAnnotation(TypeyType)
    field = StrawberryField(type_annotation=annotation)

    assert field.type is TypeyType


def test_optional():
    annotation = StrawberryAnnotation(Optional[float])
    field = StrawberryField(type_annotation=annotation)

    assert field.type == Optional[float]


def test_type_var():
    T = TypeVar("T")

    annotation = StrawberryAnnotation(T)
    field = StrawberryField(type_annotation=annotation)

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
    annotation = StrawberryAnnotation(union)
    field = StrawberryField(type_annotation=annotation)

    assert field.type is union
