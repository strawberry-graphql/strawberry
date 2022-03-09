from typing import Any

from typing_extensions import Annotated, get_args

from strawberry.auto import StrawberryAuto, auto


def test_singleton():
    assert get_args(auto)[1] is StrawberryAuto()
    assert StrawberryAuto() is StrawberryAuto()


def test_annotated():
    assert get_args(auto) == (Any, StrawberryAuto())
    some_obj = object()
    new_annotated = Annotated[auto, some_obj]
    assert get_args(new_annotated) == (Any, StrawberryAuto(), some_obj)
