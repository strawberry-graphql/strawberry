from typing import Any

import strawberry


def test_can_use_info_with_two_arguments():
    CustomInfo = strawberry.Info[int, str]

    assert CustomInfo.__args__ == (int, str)


def test_can_use_info_with_one_argument():
    CustomInfo = strawberry.Info[int]

    assert CustomInfo.__args__ == (int, Any)
