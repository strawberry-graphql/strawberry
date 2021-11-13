from enum import Enum

import strawberry
from strawberry.annotation import StrawberryAnnotation


def test_basic():
    @strawberry.enum
    class NumaNuma(Enum):
        MA = "ma"
        I = "i"  # noqa: E741
        A = "a"
        HI = "hi"

    annotation = StrawberryAnnotation(NumaNuma)
    resolved = annotation.resolve()

    assert resolved is NumaNuma
