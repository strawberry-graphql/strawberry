import textwrap

import strawberry
from strawberry.printer import print_type


def test_interface():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    expected_type = """
    interface Node {
      id: ID!
    }
    """

    assert print_type(Node("a")) == textwrap.dedent(expected_type).strip()


def test_implementing_interface():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class Post(Node):
        title: str

    expected_type = """
    type Post implements Node {
      id: ID!
      title: String!
    }
    """

    assert print_type(Post("a", "abc")) == textwrap.dedent(expected_type).strip()
