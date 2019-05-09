import textwrap

import strawberry


def test_interface():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    expected_representation = """
    interface Node {
      id: ID!
    }
    """

    assert repr(Node("a")) == textwrap.dedent(expected_representation).strip()


def test_implementing_interface():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class Post(Node):
        title: str

    expected_representation = """
    type Post implements Node {
      id: ID!
      title: String!
    }
    """

    assert repr(Post("a", "abc")) == textwrap.dedent(expected_representation).strip()
