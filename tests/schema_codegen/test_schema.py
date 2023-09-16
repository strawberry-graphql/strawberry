import textwrap

from strawberry.schema_codegen import codegen


def test_adds_schema_if_schema_is_defined():
    schema = """
    type Root {
        hello: String!
    }

    schema {
        query: Root
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Root:
            hello: str

        schema = strawberry.Schema(query=Root)
        """
    ).strip()

    assert codegen(schema).strip() == expected
