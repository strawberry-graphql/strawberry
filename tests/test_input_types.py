import textwrap
from typing import Optional

import strawberry


def test_simple_required_types():
    @strawberry.input
    class MyInput:
        s: str
        i: int
        b: bool
        f: float
        id: strawberry.ID

    expected_representation = """
    input MyInput {
      s: String!
      i: Int!
      b: Boolean!
      f: Float!
      id: ID!
    }
    """

    assert (
        repr(MyInput("a", 1, True, 3.2, "123"))
        == textwrap.dedent(expected_representation).strip()
    )
