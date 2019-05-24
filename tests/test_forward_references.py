from __future__ import annotations

import textwrap

import pytest

import strawberry


# Need to investigate this more, see: https://bugs.python.org/issue34776


@pytest.mark.xfail(strict=True, reason="Future style annotation are currently broken")
def test_forward_reference():
    @strawberry.type
    class MyType:
        id: strawberry.ID

    expected_representation = """
    type MyType {
      id: ID!
    }
    """

    assert repr(MyType("a")) == textwrap.dedent(expected_representation).strip()
