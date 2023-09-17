import textwrap

from strawberry.schema_codegen import codegen


def test_converts_query():
    schema = """
    type Query {
        hello: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Query:
            hello: str
        """
    ).strip()

    # TODO: add schema = ...

    assert codegen(schema).strip() == expected


def test_converts_mutation():
    schema = """
    type Mutation {
        hello: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Mutation:
            hello: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_converts_subscription():
    schema = """
    type Subscription {
        hello: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Subscription:
            hello: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_extend_query():
    schema = """
    extend type Query {
        world: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Query:
            world: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_extend_mutation():
    schema = """
    extend type Mutation {
        world: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Mutation:
            world: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_extend_subscription():
    schema = """
    extend type Subscription {
        world: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Subscription:
            world: str
        """
    ).strip()

    assert codegen(schema).strip() == expected
