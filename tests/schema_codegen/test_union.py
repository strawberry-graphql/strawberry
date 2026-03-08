import textwrap

from strawberry.schema_codegen import codegen


def test_union():
    schema = """
    union User = Admin | Client

    type Admin {
        name: String!
    }

    type Client {
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from typing import Annotated

        @strawberry.type
        class Admin:
            name: str

        @strawberry.type
        class Client:
            name: str

        User = Annotated[Admin | Client, strawberry.union(name="User")]
        """
    ).strip()

    assert codegen(schema).strip() == expected
