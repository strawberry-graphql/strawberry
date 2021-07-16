import sys
from typing import List, Optional, Union

import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.type import StrawberryList


def test_basic_list():
    annotation = StrawberryAnnotation(List[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == List[str]


def test_list_of_optional():
    annotation = StrawberryAnnotation(List[Optional[int]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Optional[int]

    assert resolved == StrawberryList(of_type=Optional[int])
    assert resolved == List[Optional[int]]


def test_list_of_lists():
    annotation = StrawberryAnnotation(List[List[float]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == List[float]

    assert resolved == StrawberryList(of_type=List[float])
    assert resolved == List[List[float]]


def test_list_of_union():
    @strawberry.type
    class Animal:
        feet: bool

    @strawberry.type
    class Fungus:
        spore: bool

    annotation = StrawberryAnnotation(List[Union[Animal, Fungus]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Union[Animal, Fungus]

    assert resolved == StrawberryList(of_type=Union[Animal, Fungus])
    assert resolved == List[Union[Animal, Fungus]]


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="built-in generic annotations where added in python 3.9",
)
def test_list_builtin():
    annotation = StrawberryAnnotation(list[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == List[str]
    assert resolved == list[str]
