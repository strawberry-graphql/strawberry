import textwrap

from strawberry.schema_codegen import codegen


def test_generates_used_interface_before():
    schema = """
    type Human implements Being {
        id: ID!
        name: String!
        friends: [Human]
    }

    type Cat implements Being {
        id: ID!
        name: String!
        livesLeft: Int
    }

    interface Being {
        id: ID!
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.interface
        class Being:
            id: strawberry.ID
            name: str

        @strawberry.type
        class Human(Being):
            id: strawberry.ID
            name: str
            friends: list[Human | None] | None

        @strawberry.type
        class Cat(Being):
            id: strawberry.ID
            name: str
            lives_left: int | None
        """
    ).strip()

    assert codegen(schema).strip() == expected
