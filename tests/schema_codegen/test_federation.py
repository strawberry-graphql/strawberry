import textwrap

from strawberry.schema_codegen import codegen


def test_support_for_key_directive():
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key"])

    type User @key(fields: "id") {
        id: ID!
        username: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.federation.type(keys=["id"])
        class User:
            id: strawberry.ID
            username: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_support_for_shareable_directive():
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@shareable"])

    type User @shareable {
        id: ID!
        username: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.federation.type(shareable=True)
        class User:
            id: strawberry.ID
            username: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_support_for_inaccessible_directive():
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@inaccessible"])

    type User @inaccessible {
        id: ID!
        username: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.federation.type(inaccessible=True)
        class User:
            id: strawberry.ID
            username: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_support_for_tags_directive():
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@tags"])

    type User @tag(name: "user") @tag(name: "admin") {
        id: ID!
        username: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.federation.type(tags=["user", "admin"])
        class User:
            id: strawberry.ID
            username: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_uses_federation_schema():
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@inaccessible"])

    type Query {
        me: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Query:
            me: str

        schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)
        """
    ).strip()

    assert codegen(schema).strip() == expected
