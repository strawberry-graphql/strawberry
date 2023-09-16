import textwrap

from strawberry.schema_codegen import codegen


def test_codegen_object_type():
    schema = """
    type Example {
        a: Int!
        b: Float!
        c: Boolean!
        d: String!
        e: ID!
        f: [Int!]!
        g: [Float!]!
        h: [Boolean!]!
        i: [String!]!
        j: [ID!]!
        k: [Int]
        l: [Float]
        m: [Boolean]
        n: [String]
        o: [ID]
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Example:
            a: int
            b: float
            c: bool
            d: str
            e: strawberry.ID
            f: list[int]
            g: list[float]
            h: list[bool]
            i: list[str]
            j: list[strawberry.ID]
            k: list[int | None] | None
            l: list[float | None] | None
            m: list[bool | None] | None
            n: list[str | None] | None
            o: list[strawberry.ID | None] | None
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_supports_descriptions():
    schema = """
    "Example description"
    type Example {
        "a description"
        a: Int!
        "b description"
        b: Float!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type(description="Example description")
        class Example:
            a: int = strawberry.field(description="a description")
            b: float = strawberry.field(description="b description")
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_supports_interfaces():
    schema = """
    interface Node {
        id: ID!
    }

    type User implements Node {
        id: ID!
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.interface
        class Node:
            id: strawberry.ID

        @strawberry.type
        class User(Node):
            id: strawberry.ID
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected
