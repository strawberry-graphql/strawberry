from collections.abc import Sequence
from typing import Optional, Union

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.types.base import StrawberryList


def test_basic_list():
    annotation = StrawberryAnnotation(list[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == list[str]


def test_basic_tuple():
    annotation = StrawberryAnnotation(tuple[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == tuple[str]


def test_basic_sequence():
    annotation = StrawberryAnnotation(Sequence[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == Sequence[str]


def test_list_of_optional():
    annotation = StrawberryAnnotation(list[Optional[int]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Optional[int]

    assert resolved == StrawberryList(of_type=Optional[int])
    assert resolved == list[Optional[int]]


def test_sequence_of_optional():
    annotation = StrawberryAnnotation(Sequence[Optional[int]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Optional[int]

    assert resolved == StrawberryList(of_type=Optional[int])
    assert resolved == Sequence[Optional[int]]


def test_tuple_of_optional():
    annotation = StrawberryAnnotation(tuple[Optional[int]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Optional[int]

    assert resolved == StrawberryList(of_type=Optional[int])
    assert resolved == tuple[Optional[int]]


def test_list_of_lists():
    annotation = StrawberryAnnotation(list[list[float]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == list[float]

    assert resolved == StrawberryList(of_type=list[float])
    assert resolved == list[list[float]]


def test_sequence_of_sequence():
    annotation = StrawberryAnnotation(Sequence[Sequence[float]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Sequence[float]

    assert resolved == StrawberryList(of_type=Sequence[float])
    assert resolved == Sequence[Sequence[float]]


def test_tuple_of_tuple():
    annotation = StrawberryAnnotation(tuple[tuple[float]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == tuple[float]

    assert resolved == StrawberryList(of_type=tuple[float])
    assert resolved == tuple[tuple[float]]


def test_list_of_union():
    @strawberry.type
    class Animal:
        feet: bool

    @strawberry.type
    class Fungus:
        spore: bool

    annotation = StrawberryAnnotation(list[Union[Animal, Fungus]])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type == Union[Animal, Fungus]

    assert resolved == StrawberryList(of_type=Union[Animal, Fungus])
    assert resolved == list[Union[Animal, Fungus]]


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


def test_list_builtin():
    annotation = StrawberryAnnotation(list[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == list[str]
    assert resolved == list[str]


def test_tuple_builtin():
    annotation = StrawberryAnnotation(tuple[str])
    resolved = annotation.resolve()

    assert isinstance(resolved, StrawberryList)
    assert resolved.of_type is str

    assert resolved == StrawberryList(of_type=str)
    assert resolved == tuple[str]
    assert resolved == tuple[str]
