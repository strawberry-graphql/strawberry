import textwrap

import strawberry


def test_simple_required_types():
    @strawberry.type
    class MySub:
        @strawberry.subscription
        async def x(self, info) -> str:
            return "Hi"

    expected_representation = """
    type MySub {
      x: String!
    }
    """

    assert repr(MySub()) == textwrap.dedent(expected_representation).strip()
