import textwrap

import strawberry


def test_simple_types():
    @strawberry.type
    class MyType:
        string: str
        # integer: str

    expected_representation = """
    type MyType {
      string: String!
    }
    """

    assert repr(MyType()) == textwrap.dedent(expected_representation).strip()
