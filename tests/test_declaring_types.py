import textwrap

import strawberry


def test_simple_type():
    @strawberry.type
    class MyType:
        name: str

    expected_representation = """
    type MyType {
        name: String!
    }
    """

    assert repr(MyType()) == textwrap.dedent(expected_representation).strip()
