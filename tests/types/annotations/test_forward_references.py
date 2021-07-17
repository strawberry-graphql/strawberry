import pytest

import strawberry
from strawberry.annotation import StrawberryAnnotation


def test_forward_reference():
    global ForwardClass

    annotation = StrawberryAnnotation("ForwardClass", namespace=globals())

    @strawberry.type
    class ForwardClass:
        backward: bool

    resolved = annotation.resolve()

    assert resolved is ForwardClass

    del ForwardClass


@pytest.mark.xfail(reason="Combining locals() and globals() strangely makes this fail")
def test_forward_reference_locals_and_globals():
    global BackwardClass

    namespace = {**locals(), **globals()}

    annotation = StrawberryAnnotation("BackwardClass", namespace=namespace)

    @strawberry.type
    class BackwardClass:
        backward: bool

    resolved = annotation.resolve()

    assert resolved is BackwardClass

    del BackwardClass
