import textwrap
from typing import Optional

import strawberry
from strawberry.printer import print_type


def test_simple_required_types():
    @strawberry.type
    class MyType:
        s: str
        i: int
        b: bool
        f: float
        id: strawberry.ID

    expected_type = """
    type MyType {
      s: String!
      i: Int!
      b: Boolean!
      f: Float!
      id: ID!
    }
    """

    assert (
        print_type(MyType("a", 1, True, 3.2, "123"))
        == textwrap.dedent(expected_type).strip()
    )


def test_recursive_type():
    @strawberry.type
    class MyType:
        s: "MyType"

    expected_type = """
    type MyType {
      s: MyType!
    }
    """

    assert print_type(MyType("a")) == textwrap.dedent(expected_type).strip()


def test_optional():
    @strawberry.type
    class MyType:
        s: Optional[str]

    expected_type = """
    type MyType {
      s: String
    }
    """

    assert print_type(MyType("a")) == textwrap.dedent(expected_type).strip()
