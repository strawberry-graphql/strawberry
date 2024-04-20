import textwrap

from strawberry.schema_codegen import codegen


def test_codegen_input_type():
    schema = """
    input Example {
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

        @strawberry.input
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
