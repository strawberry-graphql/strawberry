import sys
from collections.abc import Sequence
from typing import List, Optional, Tuple, Union

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


def test_basic_tuple():
    annotation = StrawberryAnnotation(Tuple[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == Tuple[str]


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="collections.abc.Sequence supporting [] was added in python 3.9",
)
def test_basic_sequence():
    annotation = StrawberryAnnotation(Sequence[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == Sequence[str]


def test_list_of_optional():
    annotation = StrawberryAnnotation(List[Optional[int]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Optional[int]

    assert resolved == StrawberryList(of_type=Optional[int])
    assert resolved == List[Optional[int]]


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="collections.abc.Sequence supporting [] was added in python 3.9",
)
def test_sequence_of_optional():
    annotation = StrawberryAnnotation(Sequence[Optional[int]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Optional[int]

    assert resolved == StrawberryList(of_type=Optional[int])
    assert resolved == Sequence[Optional[int]]


def test_tuple_of_optional():
    annotation = StrawberryAnnotation(Tuple[Optional[int]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Optional[int]

    assert resolved == StrawberryList(of_type=Optional[int])
    assert resolved == Tuple[Optional[int]]


def test_list_of_lists():
    annotation = StrawberryAnnotation(List[List[float]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == List[float]

    assert resolved == StrawberryList(of_type=List[float])
    assert resolved == List[List[float]]


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="collections.abc.Sequence supporting [] was added in python 3.9",
)
def test_sequence_of_sequence():
    annotation = StrawberryAnnotation(Sequence[Sequence[float]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Sequence[float]

    assert resolved == StrawberryList(of_type=Sequence[float])
    assert resolved == Sequence[Sequence[float]]


def test_tuple_of_tuple():
    annotation = StrawberryAnnotation(Tuple[Tuple[float]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Tuple[float]

    assert resolved == StrawberryList(of_type=Tuple[float])
    assert resolved == Tuple[Tuple[float]]


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
    reason="collections.abc.Sequence supporting [] was added in python 3.9",
)
def test_sequence_of_union():
    @strawberry.type
    class Animal:
        feet: bool

    @strawberry.type
    class Fungus:
        spore: bool

    annotation = StrawberryAnnotation(Sequence[Union[Animal, Fungus]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Union[Animal, Fungus]

    assert resolved == StrawberryList(of_type=Union[Animal, Fungus])
    assert resolved == Sequence[Union[Animal, Fungus]]


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


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="built-in generic annotations where added in python 3.9",
)
def test_tuple_builtin():
    annotation = StrawberryAnnotation(tuple[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == Tuple[str]
    assert resolved == tuple[str]
