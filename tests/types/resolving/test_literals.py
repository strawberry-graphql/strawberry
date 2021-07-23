from typing import Optional, Union

import pytest

from strawberry.annotation import StrawberryAnnotation


def test_bool():
    annotation = StrawberryAnnotation(bool)
    resolved = annotation.resolve()

    assert resolved is bool


def test_float():
    annotation = StrawberryAnnotation(float)
    resolved = annotation.resolve()

    assert resolved is float


def test_int():
    annotation = StrawberryAnnotation(int)
    resolved = annotation.resolve()

    assert resolved is int


def test_str():
    annotation = StrawberryAnnotation(str)
    resolved = annotation.resolve()

    assert resolved is str


def test_none():
    annotation = StrawberryAnnotation(None)
    with pytest.raises(ValueError, match="Annotation cannot be plain None type"):
        annotation.resolve()

    annotation = StrawberryAnnotation(Optional[int])
    annotation.resolve()

    annotation = StrawberryAnnotation(Union[None, int])
    annotation.resolve()
