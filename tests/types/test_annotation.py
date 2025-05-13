import itertools
from enum import Enum
from typing import Optional, TypeVar, Union

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.types.unset import UnsetType


class Bleh:
    pass


@strawberry.enum
class NumaNuma(Enum):
    MA = "ma"
    I = "i"  # noqa: E741
    A = "a"
    HI = "hi"


T = TypeVar("T")

types = [
    int,
    str,
    None,
    Optional[str],
    UnsetType,
    "int",
    T,
    Bleh,
    NumaNuma,
]


@pytest.mark.parametrize(
    ("type1", "type2"), itertools.combinations_with_replacement(types, 2)
)
def test_annotation_hash(type1: Union[object, str], type2: Union[object, str]):
    annotation1 = StrawberryAnnotation(type1)
    annotation2 = StrawberryAnnotation(type2)
    assert (
        hash(annotation1) == hash(annotation2)
        if annotation1 == annotation2
        else hash(annotation1) != hash(annotation2)
    ), "Equal type must imply equal hash"


def test_eq_on_other_type():
    class Foo:
        def __eq__(self, other):
            # Anything that is a strawberry annotation is equal to Foo
            return isinstance(other, StrawberryAnnotation)

    assert Foo() != object()
    assert object() != Foo()
    assert Foo() != 123 != Foo()
    assert Foo() != 123
    assert Foo() == StrawberryAnnotation(int)
    assert StrawberryAnnotation(int) == Foo()


def test_eq_on_non_annotation():
    assert StrawberryAnnotation(int) is not int
    assert StrawberryAnnotation(int) != 123


def test_set_anntation():
    annotation = StrawberryAnnotation(int)
    annotation.annotation = str

    assert annotation.annotation is str
