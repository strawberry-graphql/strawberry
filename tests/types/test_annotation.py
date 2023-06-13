import itertools
from enum import Enum
from typing import Optional, TypeVar, Union

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.unset import UnsetType


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
    Union[int, str],
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
