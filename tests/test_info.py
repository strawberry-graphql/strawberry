from typing import Any

import pytest

import strawberry


def test_can_use_info_with_two_arguments():
    CustomInfo = strawberry.Info[int, str]

    assert CustomInfo.__args__ == (int, str)


def test_can_use_info_with_one_argument():
    CustomInfo = strawberry.Info[int]

    assert CustomInfo.__args__ == (int, Any)


def test_cannot_use_info_with_more_than_two_arguments():
    with pytest.raises(
        TypeError,
        match="Too many (arguments|parameters) for <class '.*.Info'>; actual 3, expected 2",
    ):
        strawberry.Info[int, str, int]  # type: ignore
