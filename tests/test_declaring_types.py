import textwrap
from typing import Optional

import strawberry


def test_simple_required_types():
    @strawberry.type
    class MyType:
        s: str
        i: int
        b: bool
        f: float

    expected_representation = """
    type MyType {
      s: String!
      i: Int!
      b: Boolean!
      f: Float!
    }
    """

    assert repr(MyType()) == textwrap.dedent(expected_representation).strip()


def test_optional():
    @strawberry.type
    class MyType:
        s: Optional[str]

    expected_representation = """
    type MyType {
      s: String
    }
    """

    assert repr(MyType()) == textwrap.dedent(expected_representation).strip()
