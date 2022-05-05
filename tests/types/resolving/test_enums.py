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

    # TODO: Remove reference to .enum_definition with StrawberryEnum
    assert resolved is NumaNuma._enum_definition
