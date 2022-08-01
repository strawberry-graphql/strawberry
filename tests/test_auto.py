from typing import Any, cast

from typing_extensions import Annotated, get_args

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.auto import StrawberryAuto, auto
from strawberry.type import StrawberryList


@strawberry.type
class TestType:
    some_var: str


def test_singleton():
    assert get_args(auto)[1] is StrawberryAuto()
    assert StrawberryAuto() is StrawberryAuto()


def test_annotated():
    assert get_args(auto) == (Any, StrawberryAuto())
    some_obj = object()
    new_annotated = Annotated[auto, some_obj]
    assert get_args(new_annotated) == (Any, StrawberryAuto(), some_obj)


def test_str():
    assert str(StrawberryAuto()) == "auto"


def test_repr():
    assert repr(StrawberryAuto()) == "<auto>"


def test_isinstance():
    assert isinstance(auto, StrawberryAuto)
    assert not isinstance(object, StrawberryAuto)
    assert not isinstance(cast(Any, object()), StrawberryAuto)


def test_isinstance_with_annotation():
    annotation = StrawberryAnnotation(auto)
    assert isinstance(annotation, StrawberryAuto)
    str_annotation = StrawberryAnnotation("auto", namespace=globals())
    assert isinstance(str_annotation, StrawberryAuto)


def test_isinstance_with_annotated():
    assert isinstance(Annotated[auto, object()], StrawberryAuto)
    assert not isinstance(Annotated[str, auto], StrawberryAuto)


def test_isinstance_with_unresolvable_annotation():
    type_ = StrawberryList(of_type=TestType)
    assert not isinstance(type_, StrawberryAuto)
