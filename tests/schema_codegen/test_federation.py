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


def test_supports_authenticated_directive():
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@authenticated"])

    type User @authenticated {
        name: String! @authenticated
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.federation.type(authenticated=True)
        class User:
            name: str = strawberry.federation.field(authenticated=True)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_requires_scope():
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@requiresScope"])

    type User @requiresScopes(scopes: [["client", "poweruser"], ["admin"], ["productowner"]]){
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.federation.type(requires_scopes=[["client", "poweruser"], ["admin"], ["productowner"]])
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_policy_directive():
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@policy"])

    type User @policy(policies: ["userPolicy", [["client", "poweruser"], ["admin"], ["productowner"]]]){
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.federation.type(policy=["userPolicy", [["client", "poweruser"], ["admin"], ["productowner"]]])
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_support_for_directives_on_fields():
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@requires", "@provides"])

    type User {
        a: String! @shareable
        b: String! @inaccessible
        c: String! @override(from: "mySubGraph")
        c1: String! @override(from: "mySubGraph", label: "some.label")
        d: String! @external
        e: String! @requires(fields: "id")
        f: String! @provides(fields: "id")
        g: String! @tag(name: "user")
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.federation.schema_directives import Override

        @strawberry.type
        class User:
            a: str = strawberry.federation.field(shareable=True)
            b: str = strawberry.federation.field(inaccessible=True)
            c: str = strawberry.federation.field(override="mySubGraph")
            c1: str = strawberry.federation.field(override=Override(override_from="mySubGraph", label="some.label"))
            d: str = strawberry.federation.field(external=True)
            e: str = strawberry.federation.field(requires=["id"])
            f: str = strawberry.federation.field(provides=["id"])
            g: str = strawberry.federation.field(tags=["user"])
        """
    ).strip()

    assert codegen(schema).strip() == expected
