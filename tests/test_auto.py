from typing import Any

from typing_extensions import Annotated, get_args

from strawberry.annotation import StrawberryAnnotation
from strawberry.auto import StrawberryAuto, auto, is_auto


def test_singleton():
    assert get_args(auto)[1] is StrawberryAuto()
    assert StrawberryAuto() is StrawberryAuto()


def test_annotated():
    assert get_args(auto) == (Any, StrawberryAuto())
    some_obj = object()
    new_annotated = Annotated[auto, some_obj]
    assert get_args(new_annotated) == (Any, StrawberryAuto(), some_obj)


def test_is_auto():
    assert is_auto(auto) is True
    assert is_auto(object) is False
    assert is_auto(object()) is False


def test_is_auto_with_annotation():
    annotation = StrawberryAnnotation(auto)
    assert is_auto(annotation) is True
    str_annotation = StrawberryAnnotation("auto", namespace=globals())
    assert is_auto(str_annotation) is True


def test_is_auto_with_annotated():
    assert is_auto(Annotated[auto, object()]) is True
    assert is_auto(Annotated[str, auto]) is False
