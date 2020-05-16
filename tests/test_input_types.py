from typing import Optional
import textwrap

import strawberry
from strawberry.printer import print_type


def test_simple_required_types():
    @strawberry.input
    class MyInput:
        s: str
        i: int
        b: bool
        f: float
        id: strawberry.ID

    expected_type = """
    input MyInput {
      s: String!
      i: Int!
      b: Boolean!
      f: Float!
      id: ID!
    }
    """

    assert (
        print_type(MyInput("a", 1, True, 3.2, "123"))
        == textwrap.dedent(expected_type).strip()
    )


def test_optional_default():
    @strawberry.input
    class MyInput:
        s: Optional[str]
        i: int = 0

    expected_type = """
    input MyInput {
      s: String
      i: Int! = 0
    }
    """

    assert (
        print_type(MyInput("a", 1))
        == textwrap.dedent(expected_type).strip()
    )
